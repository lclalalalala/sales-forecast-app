"""
数据服务层 - DataService
=======================
负责数据集的加载、缓存和所有数据查询操作。
提供门店、商品、销售趋势、排名等数据的查询接口。

设计原则:
- 单一职责: 只负责数据访问，不包含业务逻辑
- 懒加载: 数据在首次访问时加载并缓存
- 不可变性: 返回的数据副本，防止外部修改
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class DataService:
    """
    数据服务类
    
    封装对销售数据集的所有访问操作，包括:
    - 数据加载和验证
    - 门店/商品元数据查询
    - 销售趋势聚合
    - 商品销量排名
    - 库存状态查询
    """
    
    # ─── 常量定义 ──────────────────────────────────────────────
    DATA_FILE = "sales_data.csv"
    DEFAULT_DAYS = 90  # 默认查询过去90天
    
    def __init__(self, data_path: str):
        """
        初始化数据服务
        
        Args:
            data_path: CSV数据文件的完整路径
        """
        self._data_path = data_path
        self._df: Optional[pd.DataFrame] = None
        self._stores: List[Dict] = []
        self._products: List[Dict] = []
        self._loaded = False
        
        # 自动加载数据
        self._load_data()
    
    # ═══════════════════════════════════════════════════════════
    # 私有方法: 数据加载与验证
    # ═══════════════════════════════════════════════════════════
    
    def _load_data(self) -> None:
        """
        加载并预处理CSV数据集
        
        预处理步骤:
        1. 读取CSV文件
        2. 转换日期格式
        3. 提取时间特征
        4. 缓存门店和商品列表
        5. 验证数据完整性
        """
        try:
            if not os.path.exists(self._data_path):
                raise FileNotFoundError(f"数据文件不存在: {self._data_path}")
            
            # 读取CSV
            self._df = pd.read_csv(self._data_path)
            
            # 数据验证
            required_cols = ['Date', 'Store ID', 'Product ID', 'Category', 
                           'Units Sold', 'Demand', 'Inventory Level', 'Price', 'Discount']
            missing = [c for c in required_cols if c not in self._df.columns]
            if missing:
                raise ValueError(f"CSV缺少必要列: {missing}")
            
            # 日期格式转换
            self._df['Date'] = pd.to_datetime(self._df['Date'])
            
            # 提取时间特征 (用于后续分析)
            self._df['dayofweek'] = self._df['Date'].dt.dayofweek
            self._df['month'] = self._df['Date'].dt.month
            self._df['dayofyear'] = self._df['Date'].dt.dayofyear
            self._df['year'] = self._df['Date'].dt.year
            
            # 缓存门店列表
            stores_df = self._df[['Store ID', 'Region']].drop_duplicates()
            self._stores = [
                {"id": row['Store ID'], "region": row['Region']}
                for _, row in stores_df.iterrows()
            ]
            
            # 缓存商品列表 (所有门店的商品一致)
            # 按 Product ID 去重，取每个商品的主要类别
            products_df = (self._df.groupby('Product ID')
                          .agg({'Category': 'first', 'Price': 'first'})
                          .reset_index())
            self._products = [
                {"id": row['Product ID'], "category": row['Category'], "price": row['Price']}
                for _, row in products_df.iterrows()
            ]
            
            self._loaded = True
            print(f"[DataService] 数据加载成功: {len(self._df)} 行, "
                  f"{len(self._stores)} 门店, {len(self._products)} 商品")
            
        except Exception as e:
            self._loaded = False
            print(f"[DataService] 数据加载失败: {e}")
            raise
    
    # ═══════════════════════════════════════════════════════════
    # 公共方法: 数据状态
    # ═══════════════════════════════════════════════════════════
    
    def is_loaded(self) -> bool:
        """检查数据是否成功加载"""
        return self._loaded
    
    def get_data_summary(self) -> Dict:
        """获取数据集摘要信息"""
        if not self._loaded or self._df is None:
            return {}
        return {
            "total_rows": len(self._df),
            "date_range": {
                "start": self._df['Date'].min().strftime("%Y-%m-%d"),
                "end": self._df['Date'].max().strftime("%Y-%m-%d")
            },
            "stores": len(self._stores),
            "products": len(self._products),
            "categories": self._df['Category'].nunique()
        }
    
    # ═══════════════════════════════════════════════════════════
    # 公共方法: 门店和商品查询
    # ═══════════════════════════════════════════════════════════
    
    def get_stores(self) -> List[Dict]:
        """
        获取所有门店列表
        
        Returns:
            List[Dict]: 门店列表，每项包含 id 和 region
        """
        return self._stores.copy()
    
    def get_categories(self) -> List[str]:
        """
        获取所有商品类别列表
        
        Returns:
            List[str]: 类别名称列表
        """
        if self._df is None:
            return []
        return sorted(self._df['Category'].unique().tolist())

    def get_products(self, store_id: Optional[str] = None,
                     category: Optional[str] = None) -> List[Dict]:
        """
        获取商品列表，支持类别筛选
        
        Args:
            store_id: 可选，按门店筛选
            category: 可选，按类别筛选
        
        Returns:
            List[Dict]: 商品列表，每项包含 id, category, price
        """
        products = self._products.copy()
        if category:
            products = [p for p in products if p["category"] == category]
        return products
    
    def get_product_info(self, store_id: str, product_id: str) -> Dict:
        """
        获取商品详细信息
        
        Args:
            store_id: 门店ID
            product_id: 商品ID
        
        Returns:
            Dict: 商品信息，包含 category, price 等
        """
        if self._df is None:
            return {}
        
        mask = (self._df['Store ID'] == store_id) & (self._df['Product ID'] == product_id)
        data = self._df[mask]
        
        if data.empty:
            return {"product_id": product_id, "category": "", "price": 0}
        
        return {
            "product_id": product_id,
            "category": data['Category'].iloc[0],
            "price": float(data['Price'].iloc[0])
        }
    
    # ═══════════════════════════════════════════════════════════
    # 公共方法: 销售数据查询
    # ═══════════════════════════════════════════════════════════
    
    def get_store_data(self, store_id: str, days: int = 90,
                       category: Optional[str] = None,
                       promotion: Optional[int] = None) -> pd.DataFrame:
        """
        获取指定门店最近N天的数据，支持类别和促销筛选
        
        Args:
            store_id: 门店ID
            days: 查询天数，默认90天
            category: 可选，按商品类别筛选
            promotion: 可选，按促销状态筛选 (0=否, 1=是)
        
        Returns:
            pd.DataFrame: 筛选后的数据
        """
        if self._df is None:
            return pd.DataFrame()

        # 计算日期范围
        end_date = self._df['Date'].max()
        start_date = end_date - timedelta(days=days)

        mask = (self._df['Store ID'] == store_id) & \
               (self._df['Date'] >= start_date) & \
               (self._df['Date'] <= end_date)

        if category:
            mask = mask & (self._df['Category'] == category)

        if promotion is not None:
            mask = mask & (self._df['Promotion'] == promotion)

        return self._df[mask].copy()
    
    def get_sales_trend(self, store_id: str, days: int = 90,
                        category: Optional[str] = None) -> List[Dict]:
        """
        获取门店销售趋势 (按日期聚合)，支持类别筛选
        
        Args:
            store_id: 门店ID
            days: 查询天数
            category: 可选，按商品类别筛选
        
        Returns:
            List[Dict]: 每日销售数据，包含 date, units_sold, demand
        """
        store_data = self.get_store_data(store_id, days, category=category)

        if store_data.empty:
            return []

        # 按日期聚合
        daily = store_data.groupby('Date').agg({
            'Units Sold': 'sum',
            'Demand': 'sum'
        }).reset_index()

        daily = daily.sort_values('Date')

        return [
            {
                "date": row['Date'].strftime("%Y-%m-%d"),
                "units_sold": int(row['Units Sold']),
                "demand": int(row['Demand'])
            }
            for _, row in daily.iterrows()
        ]
    
    def _get_inventory_status(self, inventory: int, avg_daily_demand: float) -> str:
        """
        计算库存状态
        
        Args:
            inventory: 当前库存
            avg_daily_demand: 日均需求
        
        Returns:
            str: 库存状态 (充足/正常/偏低/紧缺)
        """
        if avg_daily_demand <= 0:
            return "充足"
        days_left = inventory / avg_daily_demand
        if days_left > 7:
            return "充足"
        elif days_left > 3:
            return "正常"
        elif days_left > 1:
            return "偏低"
        else:
            return "紧缺"

    def get_product_ranking(self, store_id: str, days: int = 90,
                            category: Optional[str] = None,
                            inventory_status: Optional[str] = None) -> Dict:
        """
        获取商品销量排名 (Top 5 + Bottom 5)，支持类别和库存状态筛选
        
        Args:
            store_id: 门店ID
            days: 查询天数
            category: 可选，按商品类别筛选
            inventory_status: 可选，按库存状态筛选
        
        Returns:
            Dict: 包含 top_5 和 bottom_5 列表
        """
        store_data = self.get_store_data(store_id, days, category=category)

        if store_data.empty:
            return {"top_5": [], "bottom_5": []}

        # 按商品聚合
        product_stats = store_data.groupby('Product ID').agg({
            'Units Sold': 'sum',
            'Demand': 'mean',
            'Category': 'first'
        }).reset_index()

        # 获取最新库存
        latest_date = store_data['Date'].max()
        latest_inventory = store_data[store_data['Date'] == latest_date]
        inv_map = latest_inventory.groupby('Product ID')['Inventory Level'].first().to_dict()
        product_stats['inventory'] = product_stats['Product ID'].map(inv_map).fillna(0).astype(int)

        # 计算库存状态
        product_stats['inventory_status'] = product_stats.apply(
            lambda row: self._get_inventory_status(row['inventory'], row['Demand']),
            axis=1
        )

        # 库存状态筛选
        if inventory_status:
            product_stats = product_stats[
                product_stats['inventory_status'] == inventory_status
            ]

        if product_stats.empty:
            return {"top_5": [], "bottom_5": []}

        product_stats.columns = ['product_id', 'total_sold', 'demand', 'category',
                                 'inventory', 'inventory_status']
        product_stats['avg_daily'] = round(product_stats['total_sold'] / days, 1)
        product_stats = product_stats.sort_values('total_sold', ascending=False)

        # Top 5
        top_5 = product_stats.head(5)
        # Bottom 5
        bottom_5 = product_stats.tail(5).sort_values('total_sold', ascending=True)

        return {
            "top_5": [
                {
                    "product_id": row['product_id'],
                    "category": row['category'],
                    "total_sold": int(row['total_sold']),
                    "avg_daily": row['avg_daily'],
                    "inventory": int(row['inventory']),
                    "inventory_status": row['inventory_status']
                }
                for _, row in top_5.iterrows()
            ],
            "bottom_5": [
                {
                    "product_id": row['product_id'],
                    "category": row['category'],
                    "total_sold": int(row['total_sold']),
                    "avg_daily": row['avg_daily'],
                    "inventory": int(row['inventory']),
                    "inventory_status": row['inventory_status']
                }
                for _, row in bottom_5.iterrows()
            ]
        }
    
    def get_product_history(self, store_id: str, product_id: str, 
                           days: int = 90) -> List[Dict]:
        """
        获取指定商品的历史销售数据
        
        Args:
            store_id: 门店ID
            product_id: 商品ID
            days: 查询天数
        
        Returns:
            List[Dict]: 每日历史数据，包含时间特征
        """
        if self._df is None:
            return []
        
        end_date = self._df['Date'].max()
        start_date = end_date - timedelta(days=days)
        
        mask = (self._df['Store ID'] == store_id) & \
               (self._df['Product ID'] == product_id) & \
               (self._df['Date'] >= start_date) & \
               (self._df['Date'] <= end_date)
        
        data = self._df[mask].sort_values('Date')
        
        return [
            {
                "date": row['Date'].strftime("%Y-%m-%d"),
                "datetime": row['Date'],
                "units_sold": int(row['Units Sold']),
                "demand": int(row['Demand']),
                "inventory": int(row['Inventory Level']),
                "price": float(row['Price']),
                "discount": int(row['Discount']),
                "promotion": bool(row['Promotion']),
                "competitor_price": float(row['Competitor Pricing']),
                "dayofweek": int(row['dayofweek']),
                "month": int(row['month']),
                "dayofyear": int(row['dayofyear']),
                "year": int(row['year'])
            }
            for _, row in data.iterrows()
        ]
    
    # ═══════════════════════════════════════════════════════════
    # 公共方法: 库存相关查询
    # ═══════════════════════════════════════════════════════════
    
    def get_current_inventory(self, store_id: str, product_id: str) -> int:
        """
        获取商品当前库存 (最新日期的库存值)
        
        Args:
            store_id: 门店ID
            product_id: 商品ID
        
        Returns:
            int: 当前库存数量
        """
        if self._df is None:
            return 0
        
        mask = (self._df['Store ID'] == store_id) & \
               (self._df['Product ID'] == product_id)
        
        data = self._df[mask]
        if data.empty:
            return 0
        
        # 取最新日期的库存值
        latest = data.loc[data['Date'].idxmax()]
        return int(latest['Inventory Level'])
    
    def get_avg_inventory(self, store_id: str, days: int = 90) -> float:
        """
        获取门店平均库存水平
        
        Args:
            store_id: 门店ID
            days: 查询天数
        
        Returns:
            float: 平均库存数量
        """
        store_data = self.get_store_data(store_id, days)
        
        if store_data.empty:
            return 0.0
        
        # 按日期取平均库存 (所有商品的平均值)
        daily_avg = store_data.groupby('Date')['Inventory Level'].mean()
        return float(daily_avg.mean())

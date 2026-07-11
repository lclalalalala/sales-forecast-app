"""
预测服务层 - ForecastService
===========================
基于历史销售数据预测未来需求。

核心算法: 集成预测模型 (Ensemble Forecasting)
-------------------------------------------
结合多种预测方法的优点，提供更稳健的预测结果:
1. 近期均值法 - 捕捉近期水平
2. 星期模式法 - 捕捉星期周期性
3. 趋势调整 - 捕捉上升/下降趋势
4. 季节因子 - 捕捉月度季节性

算法特点:
- 无需训练，即插即用
- 对异常值鲁棒
- 可解释性强
- 计算高效

作者: AI Assistant
日期: 2026-07-11
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict


class ForecastService:
    """
    需求预测服务
    
    提供基于历史数据的未来需求预测能力。
    核心方法是 predict_next_7_days()，返回未来7天的每日预测值。
    """
    
    # ─── 算法常量 ──────────────────────────────────────────────
    SAFETY_FACTOR = 1.2       # 安全库存系数
    RECENT_DAYS = 14          # 近期天数
    TREND_CLIP_MIN = 0.7      # 趋势系数下限
    TREND_CLIP_MAX = 1.3      # 趋势系数上限
    RECENT_WEIGHT = 0.3       # 近期均值权重
    DOW_WEIGHT = 0.4          # 星期模式权重
    TREND_WEIGHT = 0.7        # 趋势调整权重 (应用于主项)
    SEASONAL_WEIGHT = 0.3     # 季节调整权重 (应用于余项)
    
    def __init__(self):
        """初始化预测服务"""
        pass
    
    # ═══════════════════════════════════════════════════════════
    # 核心方法: 7天需求预测
    # ═══════════════════════════════════════════════════════════
    
    def predict_next_7_days(self, historical_data: List[Dict]) -> List[float]:
        """
        预测未来7天的每日需求量
        
        算法流程:
        1. 计算近期均值 (最近14天)
        2. 计算星期模式 (历史同期平均)
        3. 计算趋势因子 (最近7天 vs 最近30天)
        4. 计算季节因子 (同月份历史平均)
        5. 集成预测: 加权组合上述方法
        
        Args:
            historical_data: 历史销售数据列表，每项需包含:
                - date (str): 日期字符串
                - datetime (datetime): 日期时间对象
                - demand (int): 需求量
                - dayofweek (int): 星期几 (0-6)
                - month (int): 月份 (1-12)
        
        Returns:
            List[float]: 未来7天的每日预测需求量
        """
        if not historical_data or len(historical_data) < 7:
            # 数据不足时返回基于全局平均的保守估计
            return self._fallback_prediction(historical_data)
        
        # 转换为DataFrame便于处理
        df = pd.DataFrame(historical_data)
        
        # 确保日期排序
        if 'datetime' in df.columns:
            df = df.sort_values('datetime')
        
        predictions = []
        
        for i in range(7):
            pred = self._predict_single_day(df, i)
            predictions.append(pred)
        
        return [round(p, 1) for p in predictions]
    
    # ═══════════════════════════════════════════════════════════
    # 私有方法: 单日预测
    # ═══════════════════════════════════════════════════════════
    
    def _predict_single_day(self, df: pd.DataFrame, day_offset: int) -> float:
        """
        预测未来第 N 天的需求量
        
        Args:
            df: 历史数据DataFrame
            day_offset: 偏移天数 (0=明天, 6=7天后)
        
        Returns:
            float: 预测需求量
        """
        demands = df['demand'].values
        
        # 1. 近期均值 (最近14天)
        recent_avg = np.mean(demands[-self.RECENT_DAYS:]) if len(demands) >= self.RECENT_DAYS else np.mean(demands)
        
        # 2. 目标日期的星期几
        last_date = df['datetime'].iloc[-1] if 'datetime' in df.columns else datetime.now()
        target_date = last_date + timedelta(days=day_offset + 1)
        target_dow = target_date.weekday()
        target_month = target_date.month
        
        # 3. 星期模式 (历史同期平均)
        dow_mask = df['dayofweek'] == target_dow if 'dayofweek' in df.columns else []
        if 'dayofweek' in df.columns and dow_mask.sum() >= 4:
            dow_data = df[dow_mask]['demand'].tail(8)
            dow_avg = dow_data.mean()
        else:
            dow_avg = recent_avg
        
        # 4. 趋势因子
        trend_factor = self._calculate_trend_factor(demands)
        
        # 5. 季节因子
        seasonal_factor = self._calculate_seasonal_factor(df, target_month, recent_avg)
        
        # 6. 集成预测
        # 主项: (近期均值 × 0.3 + 星期模式 × 0.4) × 趋势调整
        main_term = (recent_avg * self.RECENT_WEIGHT + 
                     dow_avg * self.DOW_WEIGHT) * trend_factor * self.TREND_WEIGHT
        
        # 余项: 近期均值 × 季节调整
        remainder_term = recent_avg * self.SEASONAL_WEIGHT * seasonal_factor
        
        prediction = main_term + remainder_term
        
        # 确保非负
        return max(0.0, prediction)
    
    # ═══════════════════════════════════════════════════════════
    # 私有方法: 辅助计算
    # ═══════════════════════════════════════════════════════════
    
    def _calculate_trend_factor(self, demands: np.ndarray) -> float:
        """
        计算趋势因子
        
        比较最近7天和最近30天的平均值，判断趋势方向。
        结果限制在 [0.7, 1.3] 范围内，防止过度反应。
        
        Args:
            demands: 需求量数组 (时间序列)
        
        Returns:
            float: 趋势因子 (1.0=平稳, >1.0=上升, <1.0=下降)
        """
        if len(demands) < 30:
            return 1.0  # 数据不足，假设平稳
        
        last_7_avg = np.mean(demands[-7:])
        last_30_avg = np.mean(demands[-30:])
        
        if last_30_avg <= 0:
            return 1.0
        
        trend = last_7_avg / last_30_avg
        
        # 限制趋势范围，防止过度调整
        return float(np.clip(trend, self.TREND_CLIP_MIN, self.TREND_CLIP_MAX))
    
    def _calculate_seasonal_factor(self, df: pd.DataFrame, 
                                    target_month: int, 
                                    recent_avg: float) -> float:
        """
        计算季节因子
        
        比较目标月份的历史平均与近期平均。
        
        Args:
            df: 历史数据DataFrame
            target_month: 目标月份 (1-12)
            recent_avg: 近期平均需求量
        
        Returns:
            float: 季节因子
        """
        if 'month' not in df.columns or recent_avg <= 0:
            return 1.0
        
        month_mask = df['month'] == target_month
        if month_mask.sum() == 0:
            return 1.0
        
        month_avg = df[month_mask]['demand'].mean()
        seasonal = month_avg / recent_avg
        
        # 限制范围
        return float(np.clip(seasonal, self.TREND_CLIP_MIN, self.TREND_CLIP_MAX))
    
    def _fallback_prediction(self, historical_data: List[Dict]) -> List[float]:
        """
        数据不足时的降级预测
        
        策略: 使用全局平均值作为保守估计
        
        Args:
            historical_data: 历史数据 (可能为空或很少)
        
        Returns:
            List[float]: 7个相同的保守预测值
        """
        if not historical_data:
            # 完全无数据时返回小正值
            return [10.0] * 7
        
        avg_demand = np.mean([d['demand'] for d in historical_data])
        conservative = max(5.0, avg_demand * 0.8)  # 保守估计
        return [round(conservative, 1)] * 7
    
    # ═══════════════════════════════════════════════════════════
    # 公共方法: 补货建议
    # ═══════════════════════════════════════════════════════════
    
    def calculate_replenishment(self, predicted_demand_7d: List[float],
                                 current_inventory: int,
                                 safety_factor: float = 1.2) -> Dict:
        """
        计算补货建议
        
        公式: 建议补货量 = max(0, 预测总需求 × 安全系数 - 当前库存)
        
        Args:
            predicted_demand_7d: 未来7天预测需求列表
            current_inventory: 当前库存数量
            safety_factor: 安全库存系数，默认1.2 (20%缓冲)
        
        Returns:
            Dict: 包含建议补货量和相关计算过程
        """
        total_predicted = sum(predicted_demand_7d)
        adjusted_demand = total_predicted * safety_factor
        suggested_qty = max(0, round(adjusted_demand - current_inventory, 1))
        
        # 库存状态评估
        if current_inventory > total_predicted * 1.5:
            status = "充足"
            status_color = "green"
        elif current_inventory > total_predicted:
            status = "正常"
            status_color = "blue"
        elif current_inventory > total_predicted * 0.5:
            status = "偏低"
            status_color = "yellow"
        else:
            status = "紧缺"
            status_color = "red"
        
        return {
            "total_predicted_demand": round(total_predicted, 1),
            "adjusted_demand": round(adjusted_demand, 1),
            "current_inventory": current_inventory,
            "suggested_replenishment": suggested_qty,
            "inventory_status": status,
            "inventory_status_color": status_color,
            "days_of_inventory": (
                round(current_inventory / (total_predicted / 7), 1)
                if total_predicted > 0 else float('inf')
            )
        }

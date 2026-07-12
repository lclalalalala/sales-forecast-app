/**
 * 销售相关类型 - Types/Sales
 * =========================
 */

export interface Store {
  id: string;
  name: string;
  region: string;
}

export interface Product {
  id: string;
  name: string;
  category: string;
}

export interface DailySales {
  date: string;
  units_sold: number;
}

export interface SalesTrendSummary {
  total_units_sold: number;
  avg_daily_sales: number;
}

export interface SalesTrendData {
  daily_sales: DailySales[];
  summary: SalesTrendSummary;
}

/** 商品销量排名 */
export interface ProductRanking {
  rank: number;
  product_id: string;
  category: string;
  total_sold: number;
  avg_daily: number;
  inventory?: number;
  inventory_status?: string;
}

/** KPI数据 */
export interface KpiData {
  store_id: string;
  period_days: number;
  total_sales: number;
  total_demand: number;
  avg_daily_sales: number;
  active_products: number;
  avg_inventory: number;
  inventory_turnover: number;
}

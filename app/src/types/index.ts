/**
 * 类型定义 - Type Definitions
 * ===========================
 * 定义全应用共享的 TypeScript 接口，确保前后端数据一致性。
 */

// ─── 基础实体 ────────────────────────────────────────────────

/** 门店信息 */
export interface Store {
  id: string;
  name: string;
  region: string;
}

/** 商品信息 */
export interface Product {
  id: string;
  name: string;
  category: string;
}

/** 每日销售数据 */
export interface DailySales {
  date: string;
  units_sold: number;
  demand: number;
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

/** 补货建议 */
export interface ReplenishmentSuggestion {
  product_id: string;
  category: string;
  current_inventory: number;
  predicted_demand_7d: number[];
  total_predicted_demand: number;
  suggested_replenishment: number;
  confidence: string;
}

/** 商品历史销售记录 */
export interface ProductHistoryRecord {
  date: string;
  units_sold: number;
  demand: number;
  inventory: number;
}

/** 商品预测数据 */
export interface ProductForecast {
  next_7_days: number[];
  total_predicted: number;
  suggested_replenishment: number;
  safety_factor: number;
}

/** 商品详情 */
export interface ProductDetail {
  product_id: string;
  category: string;
  price: number;
  current_inventory: number;
  historical_sales: ProductHistoryRecord[];
  forecast: ProductForecast;
}

// ─── API 响应格式 ────────────────────────────────────────────

/** 统一API响应 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  timestamp: string;
}

// ─── 页面数据 ────────────────────────────────────────────────

/** 销售趋势汇总 */
export interface SalesTrendSummary {
  total_units_sold: number;
  avg_daily_sales: number;
  growth_rate: number;
  data_points: number;
}

/** 销售趋势完整数据 */
export interface SalesTrendData {
  daily_sales: DailySales[];
  summary: SalesTrendSummary;
}

/** 商品排名数据 */
export interface RankingData {
  top_5: ProductRanking[];
  bottom_5: ProductRanking[];
}

/** 补货建议完整数据 */
export interface ReplenishmentData {
  store_id: string;
  forecast_date: string;
  safety_factor: number;
  top_5_products: ReplenishmentSuggestion[];
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

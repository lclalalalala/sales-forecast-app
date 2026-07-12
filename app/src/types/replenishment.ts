/**
 * 补货与预测类型 - Types/Replenishment
 * ===================================
 */

import type { InventoryStatusKey } from './api';

export interface ForecastPoint {
  date: string;
  units_sold: number;
}

export interface PredictionIntervalPoint {
  date: string;
  lower: number;
  upper: number;
}

export interface ForecastResult {
  daily_forecast_units_sold: ForecastPoint[];
  prediction_interval: PredictionIntervalPoint[];
  status: 'ready' | 'insufficient_data' | 'error' | 'forecast_unavailable';
  message: string | null;
}

export interface ReplenishmentSuggestion {
  product_id: string;
  category: string;
  current_inventory: number;
  in_transit_inventory: number;
  inventory_date: string | null;
  lead_time_k: number;
  lead_time_k_source: 'estimated' | 'default';
  forecast_7d: ForecastPoint[];
  forecast_k_total: number;
  safety_stock: number;
  suggested_replenishment: number;
  inventory_status: InventoryStatusKey;
  status: 'ready' | 'insufficient_data' | 'error' | 'forecast_unavailable';
  message: string | null;
}

export interface ReplenishmentData {
  suggestions: ReplenishmentSuggestion[];
}

export interface ProductHistoryRecord {
  date: string;
  units_sold: number;
  inventory_level: number;
  demand: number;
}

export interface ProductReplenishmentDetail {
  lead_time_k: number;
  lead_time_k_source: 'estimated' | 'default';
  forecast_k_total: number;
  safety_stock: number;
  suggested_replenishment: number;
  inventory_status: InventoryStatusKey;
}

export interface ProductDetail {
  product_id: string;
  category: string;
  price: number;
  current_inventory: number;
  in_transit_inventory: number;
  inventory_date: string | null;
  historical_sales: ProductHistoryRecord[];
  forecast: ForecastResult;
  replenishment: ProductReplenishmentDetail;
}

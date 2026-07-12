/**
 * 统一 API 类型 - Types/API
 * ========================
 */

export interface ApiError {
  code: string;
  message: string;
}

export interface ApiResponse<T> {
  context: AnalysisContext;
  data: T;
}

export interface AnalysisContext {
  store_id: string;
  category: string;
  time_range: string;
  as_of_date: string;
  actual_data_start: string;
  actual_data_end: string;
}

export type TimeRange = '7d' | '30d' | '90d' | '180d' | 'all';
export type InventoryStatusKey = 'critical' | 'low' | 'normal' | 'sufficient' | 'undetermined';

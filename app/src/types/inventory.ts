/**
 * 库存与排名类型 - Types/Inventory
 * ===============================
 */

import type { InventoryStatusKey } from './api';

export interface RankingItem {
  rank: number;
  product_id: string;
  category: string;
  total_sold: number;
  avg_daily: number;
  current_inventory: number;
  inventory_date: string | null;
  in_transit_inventory: number;
  coverage_days: number | null;
  inventory_status: InventoryStatusKey;
}

export interface RankingData {
  top: RankingItem[];
  bottom: RankingItem[];
  total_candidates: number;
}

export interface InventorySummary {
  avg_daily_units_sold: number;
  current_inventory_total: number;
  low_stock_count: number;
  critical_stock_count: number;
}

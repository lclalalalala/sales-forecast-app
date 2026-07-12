/**
 * 下单相关类型 - Types/Order
 * ==========================
 */

export interface OrderDraft {
  store_id: string;
  product_id: string;
  quantity: number;
  expected_arrival_date?: string;
  note?: string;
}

export interface OrderSubmissionResult {
  success: boolean;
  orderId: string;
}

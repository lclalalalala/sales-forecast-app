/**
 * API 服务层 - api.ts
 * ===================
 * 封装新版后端 API 调用，统一处理 `{context, data}` 响应结构。
 */

import type {
  AnalysisContext,
  ApiError,
  OrderDraft,
  OrderSubmissionResult,
  Product,
  ProductDetail,
  RankingData,
  RankingItem,
  ReplenishmentData,
  Store,
} from '@/types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8999/api';
const DEFAULT_TIMEOUT = 15_000;

interface ApiEnvelope<T> {
  context: AnalysisContext;
  data: T;
  error?: ApiError;
}

function withTimeout(controller: AbortController, ms = DEFAULT_TIMEOUT): () => void {
  const id = setTimeout(() => controller.abort(), ms);
  return () => clearTimeout(id);
}

async function fetchApi<T>(
  endpoint: string,
  params?: Record<string, string | undefined>,
  signal?: AbortSignal
): Promise<{ context: AnalysisContext; data: T }> {
  // API_BASE 可能是绝对地址（开发态 http://localhost:8999/api）或相对路径（打包态 /api）。
  // 传入 window.location.origin 作为 base：绝对地址时被忽略，相对路径时按当前源解析，
  // 避免 new URL('/api/stores') 因缺少 base 抛 "cannot be parsed as a URL"。
  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.append(key, String(value));
      }
    });
  }

  const controller = new AbortController();
  const clear = withTimeout(controller, DEFAULT_TIMEOUT);
  signal?.addEventListener('abort', () => controller.abort(), { once: true });

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`API 请求失败: ${response.status} ${response.statusText}`);
    }

    const result: ApiEnvelope<T> = await response.json();

    if (result.error) {
      throw new Error(result.error.message || `API 错误: ${result.error.code}`);
    }

    if (result.data === undefined) {
      throw new Error('API 响应缺少 data 字段');
    }

    return { context: result.context, data: result.data };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      if (signal?.aborted) throw err;
      throw new Error('请求超时，请稍后重试');
    }
    throw err;
  } finally {
    clear();
  }
}

export async function getStores(signal?: AbortSignal): Promise<Store[]> {
  return fetchApi<Store[]>('/stores', undefined, signal).then((r) => r.data ?? []);
}

export async function getCategories(signal?: AbortSignal): Promise<string[]> {
  return fetchApi<string[]>('/categories', undefined, signal).then((r) => r.data ?? []);
}

export async function getProducts(
  storeId?: string,
  category?: string,
  signal?: AbortSignal
): Promise<Product[]> {
  return fetchApi<Product[]>(
    '/products',
    { store_id: storeId, category },
    signal
  ).then((r) => r.data ?? []);
}

export async function getOverview(
  storeId: string,
  range: string,
  category?: string,
  signal?: AbortSignal
): Promise<{ context: AnalysisContext; data: {
  kpis: {
    avg_daily_units_sold: number;
    current_inventory_total: number;
    low_stock_count: number;
    critical_stock_count: number;
  };
  daily_sales: { date: string; units_sold: number }[];
  top_products: RankingItem[];
  bottom_products: RankingItem[];
  data_date_note: string | null;
} }> {
  return fetchApi('/overview', { store_id: storeId, range, category }, signal);
}

export async function getRankings(
  storeId: string,
  range: string,
  category?: string,
  inventoryStatus?: string,
  topN?: number,
  bottomN?: number,
  signal?: AbortSignal
): Promise<{ context: AnalysisContext; data: RankingData }> {
  return fetchApi('/rankings', {
    store_id: storeId,
    range,
    category,
    inventory_status: inventoryStatus,
    top_n: topN !== undefined ? String(topN) : undefined,
    bottom_n: bottomN !== undefined ? String(bottomN) : undefined,
  }, signal);
}

export async function getReplenishment(
  storeId: string,
  category?: string,
  signal?: AbortSignal
): Promise<{ context: AnalysisContext; data: ReplenishmentData }> {
  return fetchApi('/replenishment', { store_id: storeId, category }, signal);
}

export async function getProductDetail(
  productId: string,
  storeId: string,
  range: string,
  signal?: AbortSignal
): Promise<{ context: AnalysisContext; data: ProductDetail }> {
  return fetchApi(`/products/${encodeURIComponent(productId)}`, {
    store_id: storeId,
    range,
  }, signal);
}

export async function submitOrder(draft: OrderDraft): Promise<OrderSubmissionResult> {
  void draft;
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        orderId: `ORD-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      });
    }, 400);
  });
}

export const api = {
  getStores,
  getCategories,
  getProducts,
  getOverview,
  getRankings,
  getReplenishment,
  getProductDetail,
  submitOrder,
};

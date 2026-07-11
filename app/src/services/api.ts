/**
 * API 服务层 - api.ts
 * ===================
 * 封装所有后端 API 调用，提供类型安全的请求方法。
 *
 * 使用说明:
 *   import { api } from '@/services/api';
 *   const stores = await api.getStores();
 */

import type {
  ApiResponse,
  Store,
  Product,
  SalesTrendData,
  RankingData,
  ReplenishmentData,
  ProductDetail,
  KpiData,
} from '@/types';

// ─── 常量配置 ────────────────────────────────────────────────

/** API 基础地址，支持通过环境变量覆盖 */
const API_BASE = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8999/api';

/** 默认请求超时 (ms) */
const DEFAULT_TIMEOUT = 15_000;

// ─── 辅助函数 ────────────────────────────────────────────────

/**
 * 创建带超时控制的 AbortSignal
 */
function withTimeout(controller: AbortController, ms = DEFAULT_TIMEOUT): () => void {
  const id = setTimeout(() => controller.abort(), ms);
  return () => clearTimeout(id);
}

/**
 * 统一发起 API 请求
 *
 * @param endpoint - API 端点路径 (不含前缀)
 * @param params - 可选的查询参数
 * @param signal - 可选的 AbortSignal，用于请求取消
 * @returns 解析后的 JSON 数据
 * @throws 请求失败时抛出错误
 */
async function fetchApi<T>(
  endpoint: string,
  params?: Record<string, string>,
  signal?: AbortSignal
): Promise<T> {
  // 构建完整 URL
  const url = new URL(`${API_BASE}${endpoint}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.append(key, String(value));
      }
    });
  }

  // 合并外部 signal 与超时控制
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

    const result: ApiResponse<T> = await response.json();

    if (!result.success) {
      throw new Error(result.message || 'API 返回错误');
    }

    return result.data;
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      // 外部主动取消时保留 AbortError，让调用方忽略；超时则转换为用户友好错误
      if (signal?.aborted) throw err;
      throw new Error('请求超时，请稍后重试');
    }
    throw err;
  } finally {
    clear();
  }
}

// ═══════════════════════════════════════════════════════════════
// API 方法
// ═══════════════════════════════════════════════════════════════

/**
 * 获取所有门店列表
 */
export async function getStores(signal?: AbortSignal): Promise<Store[]> {
  return fetchApi<Store[]>('/stores', undefined, signal);
}

/**
 * 获取所有商品类别列表
 */
export async function getCategories(signal?: AbortSignal): Promise<string[]> {
  return fetchApi<string[]>('/categories', undefined, signal);
}

/**
 * 获取商品列表，支持类别筛选
 * @param storeId - 门店ID (可选)
 * @param category - 商品类别 (可选)
 */
export async function getProducts(storeId?: string, category?: string, signal?: AbortSignal): Promise<Product[]> {
  const params: Record<string, string> = {};
  if (storeId) params.store_id = storeId;
  if (category) params.category = category;
  return fetchApi<Product[]>('/products', params, signal);
}

/**
 * 获取门店销售趋势，支持类别筛选
 * @param storeId - 门店ID
 * @param days - 查询天数 (默认90)
 * @param category - 商品类别 (可选)
 */
export async function getSalesTrend(storeId: string, days: number = 90, category?: string, signal?: AbortSignal): Promise<SalesTrendData> {
  const params: Record<string, string> = {
    store_id: storeId,
    days: String(days),
  };
  if (category) params.category = category;
  return fetchApi<SalesTrendData>('/sales/trend', params, signal);
}

/**
 * 获取商品销量排名 (Top 5 + Bottom 5)，支持类别和库存状态筛选
 * @param storeId - 门店ID
 * @param days - 查询天数 (默认90)
 * @param category - 商品类别 (可选)
 * @param inventoryStatus - 库存状态 (可选)
 */
export async function getSalesRanking(storeId: string, days: number = 90, category?: string, inventoryStatus?: string, signal?: AbortSignal): Promise<RankingData> {
  const params: Record<string, string> = {
    store_id: storeId,
    days: String(days),
  };
  if (category) params.category = category;
  if (inventoryStatus) params.inventory_status = inventoryStatus;
  return fetchApi<RankingData>('/sales/ranking', params, signal);
}

/**
 * 获取补货建议
 * @param storeId - 门店ID
 * @param safetyFactor - 安全库存系数 (默认1.2)
 */
export async function getReplenishment(storeId: string, safetyFactor: number = 1.2, signal?: AbortSignal): Promise<ReplenishmentData> {
  return fetchApi<ReplenishmentData>('/replenishment', {
    store_id: storeId,
    safety_factor: String(safetyFactor),
  }, signal);
}

/**
 * 获取商品详情
 * @param storeId - 门店ID
 * @param productId - 商品ID
 * @param days - 历史数据天数 (默认90)
 */
export async function getProductDetail(
  storeId: string,
  productId: string,
  days: number = 90,
  signal?: AbortSignal
): Promise<ProductDetail> {
  return fetchApi<ProductDetail>('/products/detail', {
    store_id: storeId,
    product_id: productId,
    days: String(days),
  }, signal);
}

/**
 * 获取KPI数据
 * @param storeId - 门店ID
 * @param days - 查询天数 (默认90)
 */
export async function getDashboardKpi(storeId: string, days: number = 90, signal?: AbortSignal): Promise<KpiData> {
  return fetchApi<KpiData>('/dashboard/kpi', {
    store_id: storeId,
    days: String(days),
  }, signal);
}

// ─── 导出统一对象 ────────────────────────────────────────────

/**
 * API 统一入口
 *
 * 使用示例:
 *   import { api } from '@/services/api';
 *   const stores = await api.getStores();
 */
export const api = {
  getStores,
  getCategories,
  getProducts,
  getSalesTrend,
  getSalesRanking,
  getReplenishment,
  getProductDetail,
  getDashboardKpi,
};

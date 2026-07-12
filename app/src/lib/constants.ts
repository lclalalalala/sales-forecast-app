/**
 * 全局常量 - constants.ts
 * =======================
 * 集中管理跨文件共享的魔法字符串与数字。
 */

/** URL 查询参数名 */
export const PARAM_STORE_ID = 'store_id';
export const PARAM_PRODUCT_ID = 'product_id';
export const PARAM_QUANTITY = 'quantity';

/** 默认值 */
export const DEFAULT_PRODUCT_ID = 'P0001';
export const DEFAULT_TIME_RANGE = '90d' as const;

/** 展示限制 */
export const ALL_TIME_RANGE_DAYS = 1000;
export const REPLENISHMENT_DISPLAY_LIMIT = 50;

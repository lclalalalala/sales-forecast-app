/**
 * 数值与日期格式化工具 - format.ts
 * ================================
 * 集中管理跨页面复用的数字/日期格式化，避免各文件各自实现导致行为不一致。
 */

/** 整数千分位格式化；null/undefined/非有限值（NaN、Infinity）返回 '-' */
export function formatInt(n?: number | null): string {
  return n != null && Number.isFinite(n) ? n.toLocaleString('zh-CN') : '-';
}

/** 保留指定小数位（默认 1 位）；null/undefined/非有限值返回 '-' */
export function formatDecimal(n?: number | null, digits = 1): string {
  return n != null && Number.isFinite(n) ? n.toFixed(digits) : '-';
}

/**
 * 以本地时区格式化为 YYYY-MM-DD。
 * 不使用 Date.toISOString()，避免其转 UTC 后在东八区等时区产生 off-by-one 日期偏移。
 */
export function formatLocalDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

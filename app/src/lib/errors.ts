/**
 * 错误处理工具 - errors.ts
 * ========================
 * 统一的 catch 块类型守卫，替代 `(e as Error)?.name` 模式。
 */

/** 判断异常是否为 AbortError（用于取消请求场景） */
export function isAbortError(e: unknown): boolean {
  return e instanceof Error && e.name === 'AbortError';
}

/** 安全提取异常的 message，非 Error 类型返回 fallback */
export function getErrorMessage(e: unknown, fallback = '操作失败，请稍后重试'): string {
  if (e instanceof Error && e.message) return e.message;
  if (typeof e === 'string' && e) return e;
  return fallback;
}

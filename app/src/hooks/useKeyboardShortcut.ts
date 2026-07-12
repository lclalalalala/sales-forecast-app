/**
 * useKeyboardShortcut 键盘快捷键 hook
 * ===================================
 * 封装 keydown 监听，支持组合键（Ctrl/Cmd/Alt/Shift）与单键。
 */

import { useEffect, useRef } from 'react';

export interface KeyboardShortcutOptions {
  /** 主键，例如 'k', 'Escape', 'Enter' */
  key: string;
  /** 是否需要 Ctrl/Cmd */
  meta?: boolean;
  /** 是否需要 Ctrl */
  ctrl?: boolean;
  /** 是否需要 Alt/Option */
  alt?: boolean;
  /** 是否需要 Shift */
  shift?: boolean;
  /** 是否阻止默认行为 */
  preventDefault?: boolean;
  /** 是否阻止冒泡 */
  stopPropagation?: boolean;
}

export default function useKeyboardShortcut(
  callback: () => void,
  options: KeyboardShortcutOptions,
) {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  });

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const {
        key,
        meta = false,
        ctrl = false,
        alt = false,
        shift = false,
        preventDefault = false,
        stopPropagation = false,
      } = options;

      const normalizedEventKey = event.key.length === 1 ? event.key.toLowerCase() : event.key;
      const normalizedTargetKey = key.length === 1 ? key.toLowerCase() : key;

      if (normalizedEventKey !== normalizedTargetKey) return;

      const target = event.target;
      if (
        target instanceof HTMLElement &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.tagName === 'SELECT' ||
          target.isContentEditable)
      ) {
        return;
      }

      if (meta && !(event.metaKey || event.ctrlKey)) return;
      if (ctrl && !event.ctrlKey) return;
      if (alt && !event.altKey) return;
      if (shift && !event.shiftKey) return;

      if (preventDefault) event.preventDefault();
      if (stopPropagation) event.stopPropagation();
      callbackRef.current();
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [options]);
}

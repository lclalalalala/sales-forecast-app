/**
 * 格式化工具测试 - format.test.ts
 * ================================
 */

import { describe, it, expect } from 'vitest';
import { formatInt, formatDecimal, formatLocalDate } from '@/lib/format';

describe('formatInt', () => {
  it('千分位格式化整数', () => {
    expect(formatInt(1234567)).toBe('1,234,567');
  });

  it('非有限值 / null / undefined 返回 -', () => {
    expect(formatInt(null)).toBe('-');
    expect(formatInt(undefined)).toBe('-');
    expect(formatInt(NaN)).toBe('-');
    expect(formatInt(Infinity)).toBe('-');
  });

  it('0 正常显示而非 -', () => {
    expect(formatInt(0)).toBe('0');
  });
});

describe('formatDecimal', () => {
  it('默认保留 1 位小数', () => {
    expect(formatDecimal(3.14159)).toBe('3.1');
  });

  it('可指定小数位', () => {
    expect(formatDecimal(3.14159, 2)).toBe('3.14');
  });

  it('非有限值 / null 返回 -', () => {
    expect(formatDecimal(null)).toBe('-');
    expect(formatDecimal(NaN)).toBe('-');
    expect(formatDecimal(Infinity, 2)).toBe('-');
  });
});

describe('formatLocalDate', () => {
  it('按本地时区输出 YYYY-MM-DD，不受 UTC 偏移影响', () => {
    // 构造本地时间当天的午夜与深夜，本地日期应保持一致
    const local = new Date(2026, 6, 13, 0, 0, 0); // 2026-07-13 本地 00:00
    expect(formatLocalDate(local)).toBe('2026-07-13');

    const lateNight = new Date(2026, 6, 13, 23, 30, 0); // 2026-07-13 本地 23:30
    // toISOString().slice(0,10) 在东八区会得到 2026-07-14（错误），本地格式化应仍为 13 号
    expect(formatLocalDate(lateNight)).toBe('2026-07-13');
  });

  it('月 / 日补零', () => {
    const d = new Date(2026, 0, 5, 12, 0, 0); // 2026-01-05
    expect(formatLocalDate(d)).toBe('2026-01-05');
  });
});

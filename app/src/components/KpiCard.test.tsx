/**
 * KpiCard 组件测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Package } from 'lucide-react';
import KpiCard from '@/components/KpiCard';

describe('KpiCard', () => {
  it('渲染标签、数值与辅助说明', () => {
    render(<KpiCard icon={Package} label="测试指标" value="1,234" subtext="辅助说明" />);

    expect(screen.getByText('测试指标')).toBeInTheDocument();
    expect(screen.getByText('1,234')).toBeInTheDocument();
    expect(screen.getByText('辅助说明')).toBeInTheDocument();
  });

  it('无辅助说明时不渲染 subtext 区域', () => {
    render(<KpiCard icon={Package} label="测试指标" value="value" />);

    expect(screen.queryByText('辅助说明')).not.toBeInTheDocument();
  });
});

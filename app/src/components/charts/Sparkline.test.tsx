/**
 * Sparkline 组件测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Sparkline from '@/components/charts/Sparkline';

describe('Sparkline', () => {
  it('有数据时渲染图表容器', () => {
    render(<Sparkline data={[1, 2, 3, 4]} labels={['a', 'b', 'c', 'd']} />);

    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('空数据时显示无数据提示', () => {
    render(<Sparkline data={[]} />);

    expect(screen.getByText('无数据')).toBeInTheDocument();
  });

  it('全零数据时仍然渲染图表容器', () => {
    render(<Sparkline data={[0, 0, 0]} />);

    expect(screen.getByRole('img')).toBeInTheDocument();
  });
});

/**
 * ThemeToggle 组件测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from 'next-themes';
import ThemeToggle from '@/components/ThemeToggle';

function Wrapper({ children }: { children: React.ReactNode }) {
  return <ThemeProvider attribute="class" defaultTheme="system">{children}</ThemeProvider>;
}

describe('ThemeToggle', () => {
  it('打开下拉菜单并展示 light / dark / system 选项', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />, { wrapper: Wrapper });

    const trigger = screen.getByRole('button', { name: /切换主题/ });
    await user.click(trigger);

    expect(screen.getByRole('menuitem', { name: '浅色' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: '深色' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: '跟随系统' })).toBeInTheDocument();
  });

  it('切换主题会修改 html 元素的 theme class', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />, { wrapper: Wrapper });

    const trigger = screen.getByRole('button', { name: /切换主题/ });
    await user.click(trigger);

    await user.click(screen.getByRole('menuitem', { name: '深色' }));
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    await user.click(trigger);
    await user.click(screen.getByRole('menuitem', { name: '浅色' }));
    expect(document.documentElement.classList.contains('light')).toBe(true);
  });
});

/**
 * HelpDrawer 组件测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import HelpDrawer from '@/components/HelpDrawer';

function Wrapper({ children }: { children: React.ReactNode }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe('HelpDrawer', () => {
  it('点击帮助按钮后展示补货系统说明', async () => {
    const user = userEvent.setup();
    render(<HelpDrawer />, { wrapper: Wrapper });

    const trigger = screen.getByRole('button', { name: /打开帮助说明/ });
    await user.click(trigger);

    expect(screen.getByText('补货系统说明')).toBeInTheDocument();
    expect(screen.getByText('核心概念')).toBeInTheDocument();
    expect(screen.getByText('补货计算')).toBeInTheDocument();
    expect(screen.getByText('查看完整补货系统说明文档')).toBeInTheDocument();
  });

  it('打开后可通过 Esc 关闭并归还焦点到触发按钮', async () => {
    const user = userEvent.setup();
    render(<HelpDrawer />, { wrapper: Wrapper });

    const trigger = screen.getByRole('button', { name: /打开帮助说明/ });
    await user.click(trigger);

    const dialog = await screen.findByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(dialog.contains(document.activeElement)).toBe(true);

    await user.keyboard('{Escape}');
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    expect(trigger).toHaveFocus();
  });
});

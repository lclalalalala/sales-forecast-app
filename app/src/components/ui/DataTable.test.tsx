/**
 * DataTable 组件测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable';

interface Row {
  name: string;
  value: number;
}

const columns: DataTableColumn<Row>[] = [
  { key: 'name', header: '名称', sortable: true, render: (r) => r.name },
  { key: 'value', header: '数值', align: 'right', sortable: true, render: (r) => r.value },
];

const data: Row[] = [
  { name: 'B', value: 20 },
  { name: 'A', value: 10 },
  { name: 'C', value: 30 },
];

describe('DataTable', () => {
  it('渲染表头与数据行', () => {
    render(<DataTable columns={columns} data={data} rowKey={(r) => r.name} />);

    expect(screen.getByText('名称')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('点击表头按数值降序再升序排序', async () => {
    render(<DataTable columns={columns} data={data} rowKey={(r) => r.name} />);

    const valueHeader = screen.getByRole('button', { name: '数值' });
    await userEvent.click(valueHeader);

    const cells = screen.getAllByRole('cell').filter((c) => c.textContent?.match(/^\d+$/));
    expect(cells.map((c) => c.textContent)).toEqual(['30', '20', '10']);

    await userEvent.click(valueHeader);
    const cellsAsc = screen.getAllByRole('cell').filter((c) => c.textContent?.match(/^\d+$/));
    expect(cellsAsc.map((c) => c.textContent)).toEqual(['10', '20', '30']);
  });

  it('排序表头暴露 aria-sort 且可通过键盘 Enter 触发', async () => {
    render(<DataTable columns={columns} data={data} rowKey={(r) => r.name} />);

    const nameHeader = screen.getByRole('button', { name: '名称' });
    expect(nameHeader.closest('th')).toHaveAttribute('aria-sort', 'none');

    await userEvent.keyboard('{Tab}');
    expect(nameHeader).toHaveFocus();
    await userEvent.keyboard('{Enter}');

    const cells = screen.getAllByRole('cell').filter((c) => /^[A-Z]$/.test(c.textContent || ''));
    expect(cells.map((c) => c.textContent)).toEqual(['C', 'B', 'A']);
    expect(nameHeader.closest('th')).toHaveAttribute('aria-sort', 'descending');
  });

  it('空数据时显示空状态', () => {
    render(<DataTable columns={columns} data={[]} rowKey={(r) => r.name} />);

    expect(screen.getByText('当前筛选条件下暂无商品数据')).toBeInTheDocument();
  });
});

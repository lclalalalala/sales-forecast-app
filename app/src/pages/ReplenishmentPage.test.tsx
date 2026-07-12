/**
 * 补货建议页测试 - ReplenishmentPage.test.tsx
 * ===========================================
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AnalysisProvider } from '@/state/analysisContext';
import ReplenishmentPage from '@/pages/ReplenishmentPage';
import { api } from '@/services/api';
import type { ReplenishmentData, Store, ProductDetail } from '@/types';

const mockStores: Store[] = [
  { id: 'S001', name: '旗舰店', region: '华东' },
];

const mockReplenishment: ReplenishmentData = {
  suggestions: [
    {
      product_id: 'P0003',
      category: 'Furniture',
      current_inventory: 111,
      in_transit_inventory: 0,
      inventory_date: '2026-07-10',
      lead_time_k: 2,
      lead_time_k_source: 'estimated',
      forecast_7d: [],
      forecast_k_total: 134.8,
      safety_stock: 127,
      suggested_replenishment: 151,
      inventory_status: 'critical',
      status: 'ready',
      message: null,
    },
    {
      product_id: 'P0020',
      category: 'Furniture',
      current_inventory: 0,
      in_transit_inventory: 0,
      inventory_date: null,
      lead_time_k: 1,
      lead_time_k_source: 'default',
      forecast_7d: [],
      forecast_k_total: 54.1,
      safety_stock: 69,
      suggested_replenishment: 124,
      inventory_status: 'low',
      status: 'ready',
      message: null,
    },
    {
      product_id: 'P0099',
      category: 'Groceries',
      current_inventory: 500,
      in_transit_inventory: 0,
      inventory_date: '2026-07-10',
      lead_time_k: 2,
      lead_time_k_source: 'estimated',
      forecast_7d: [],
      forecast_k_total: 10.0,
      safety_stock: 20,
      suggested_replenishment: 0,
      inventory_status: 'normal',
      status: 'ready',
      message: null,
    },
  ],
};

const mockProductDetail: ProductDetail = {
  product_id: 'P0003',
  category: 'Furniture',
  price: 99.9,
  current_inventory: 111,
  in_transit_inventory: 0,
  inventory_date: '2026-07-12',
  historical_sales: [],
  forecast: {
    daily_forecast_units_sold: [],
    prediction_interval: [],
    status: 'ready',
    message: null,
  },
  replenishment: {
    lead_time_k: 2,
    lead_time_k_source: 'estimated',
    forecast_k_total: 134.8,
    safety_stock: 127,
    suggested_replenishment: 151,
    inventory_status: 'critical',
  },
};

vi.mock('@/services/api', () => ({
  api: {
    getStores: vi.fn(() => Promise.resolve(mockStores)),
    getCategories: vi.fn(() => Promise.resolve(['Furniture', 'Groceries'])),
    getProductDetail: vi.fn(() => Promise.resolve({ context: {} as never, data: mockProductDetail })),
    getReplenishment: vi.fn(() =>
      Promise.resolve({
        context: {
          store_id: 'S001',
          category: '',
          time_range: '90d',
          as_of_date: '2026-07-12',
          actual_data_start: '2026-04-13',
          actual_data_end: '2026-07-12',
        },
        data: mockReplenishment,
      })
    ),
  },
}));

function renderReplenishmentPage() {
  return render(
    <MemoryRouter initialEntries={['/replenishment']}>
      <AnalysisProvider>
        <Routes>
          <Route path="/replenishment" element={<ReplenishmentPage />} />
        </Routes>
      </AnalysisProvider>
    </MemoryRouter>
  );
}

describe('ReplenishmentPage', () => {
  it('表格每行末尾显示“去下单”按钮，点击后以弹层形式打开补货表单', async () => {
    const user = userEvent.setup();
    renderReplenishmentPage();

    await waitFor(() => {
      const buttons = screen.getAllByRole('button', { name: /去下单/ });
      expect(buttons).toHaveLength(mockReplenishment.suggestions.length);
    });

    const buttons = screen.getAllByRole('button', { name: /去下单/ });
    await user.click(buttons[0]);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    expect(screen.getByText('补货下单')).toBeInTheDocument();
    expect(screen.getByDisplayValue('P0003')).toBeInTheDocument();
    expect(screen.getByDisplayValue('151')).toBeInTheDocument();
  });

  it('快速筛选：全部商品 / 待补货', async () => {
    const user = userEvent.setup();
    renderReplenishmentPage();

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /去下单/ })).toHaveLength(3);
    });

    await user.click(screen.getByRole('button', { name: '待补货' }));
    expect(screen.getAllByRole('button', { name: /去下单/ })).toHaveLength(2);

    await user.click(screen.getByRole('button', { name: '全部商品' }));
    expect(screen.getAllByRole('button', { name: /去下单/ })).toHaveLength(3);
  });

  it('点击“建议补货量”表头可切换升降序', async () => {
    const user = userEvent.setup();
    renderReplenishmentPage();

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /去下单/ })).toHaveLength(3);
    });

    const getIds = () =>
      screen
        .getAllByRole('link')
        .filter((el) => /^P\d+$/.test(el.textContent || ''))
        .map((el) => el.textContent);

    expect(getIds()).toEqual(['P0003', 'P0020', 'P0099']);

    const header = screen.getByRole('button', { name: '建议补货量' });
    await user.click(header);
    expect(getIds()).toEqual(['P0003', 'P0020', 'P0099']);

    await user.click(header);
    expect(getIds()).toEqual(['P0099', 'P0020', 'P0003']);
  });

  it('无建议时显示空状态', async () => {
    vi.mocked(api.getReplenishment).mockResolvedValueOnce({
      context: {
        store_id: 'S001',
        category: '',
        time_range: '90d',
        as_of_date: '2026-07-12',
        actual_data_start: '2026-04-13',
        actual_data_end: '2026-07-12',
      },
      data: { suggestions: [] },
    });
    renderReplenishmentPage();

    await waitFor(() => {
      expect(screen.getByText('当前筛选条件下暂无商品数据')).toBeInTheDocument();
    });
  });

  it('加载失败时展示错误并可重试', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getReplenishment).mockRejectedValueOnce(new Error('网络错误'));
    renderReplenishmentPage();

    await waitFor(() => {
      expect(screen.getByText('网络错误')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: '重新加载' }));

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /去下单/ })).toHaveLength(3);
    });
  });
});

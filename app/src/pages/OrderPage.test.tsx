/**
 * 补货下单详情页测试 - OrderPage.test.tsx
 * ========================================
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AnalysisProvider } from '@/state/analysisContext';
import OrderPage from '@/pages/OrderPage';
import * as apiModule from '@/services/api';
import { api } from '@/services/api';
import type { ProductDetail } from '@/types';

const mockStores = [
  { id: 'S001', name: '旗舰店', region: '华东' },
  { id: 'S002', name: '社区店', region: '华北' },
];

const mockProductDetail: ProductDetail = {
  product_id: 'P0001',
  category: 'Furniture',
  price: 99.9,
  current_inventory: 10,
  in_transit_inventory: 2,
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
    forecast_k_total: 20,
    safety_stock: 5,
    suggested_replenishment: 13,
    inventory_status: 'low',
  },
};

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof apiModule>('@/services/api');
  const mockedSubmitOrder = vi.fn();
  const mockedGetProductDetail = vi.fn(() => Promise.resolve({ context: {} as never, data: mockProductDetail }));
  return {
    ...actual,
    api: {
      ...actual.api,
      getStores: vi.fn(() => Promise.resolve(mockStores)),
      getProductDetail: mockedGetProductDetail,
      submitOrder: mockedSubmitOrder,
    },
  };
});

const mockSubmitOrder = vi.mocked(api.submitOrder);
const mockGetProductDetail = vi.mocked(api.getProductDetail);

function renderOrderPage(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AnalysisProvider>
        <Routes>
          <Route path="/orders/new" element={<OrderPage />} />
          <Route path="/replenishment" element={<div data-testid="replenishment">补货建议</div>} />
        </Routes>
      </AnalysisProvider>
    </MemoryRouter>,
  );
}

async function waitForPageReady() {
  await waitFor(() => {
    expect(screen.getByRole('combobox')).toHaveTextContent(/旗舰店|社区店/);
  });
  await waitFor(() => {
    expect(screen.getByText('补货依据', { selector: 'label' })).toBeInTheDocument();
  });
}

describe('OrderPage', () => {
  beforeEach(() => {
    mockSubmitOrder.mockReset();
    mockSubmitOrder.mockResolvedValue({ success: true, orderId: 'ORD-12345' });
    mockGetProductDetail.mockResolvedValue({ context: {} as never, data: mockProductDetail });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('从 query string 预填门店、商品 ID 与数量', async () => {
    renderOrderPage('/orders/new?store_id=S002&product_id=P0003&quantity=42');

    await waitForPageReady();
    expect(screen.getByRole('combobox')).toHaveTextContent(/社区店/);
    expect(screen.getByDisplayValue('P0003')).toBeInTheDocument();
    expect(screen.getByDisplayValue('42')).toBeInTheDocument();
  });

  it('数量字段可由店长修改', async () => {
    const user = userEvent.setup();
    renderOrderPage('/orders/new?store_id=S001&product_id=P0001&quantity=10');

    await waitForPageReady();
    const quantityInput = screen.getByLabelText(/补货数量/);
    await user.clear(quantityInput);
    await user.type(quantityInput, '25');

    expect(quantityInput).toHaveValue(25);
  });

  it('非法数量会禁用提交按钮', async () => {
    const user = userEvent.setup();
    renderOrderPage('/orders/new?store_id=S001&product_id=P0001&quantity=10');

    await waitForPageReady();
    const quantityInput = screen.getByLabelText(/补货数量/);
    await user.clear(quantityInput);
    await user.type(quantityInput, '1.5');

    expect(screen.getByRole('button', { name: '确认补货' })).toBeDisabled();
  });

  it('点击确认补货后调用 api.submitOrder 并显示成功', async () => {
    const user = userEvent.setup();
    renderOrderPage('/orders/new?store_id=S001&product_id=P0001&quantity=10');

    await waitForPageReady();
    const submitBtn = screen.getByRole('button', { name: '确认补货' });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('已生成补货记录')).toBeInTheDocument();
    });

    expect(mockSubmitOrder).toHaveBeenCalledWith(
      expect.objectContaining({
        store_id: 'S001',
        product_id: 'P0001',
        quantity: 10,
      }),
    );
    expect(screen.getByText(/ORD-12345/)).toBeInTheDocument();
  });

  it('提交失败时展示错误提示', async () => {
    mockSubmitOrder.mockRejectedValue(new Error('网络错误'));
    const user = userEvent.setup();
    renderOrderPage('/orders/new?store_id=S001&product_id=P0001&quantity=10');

    await waitForPageReady();
    await user.click(screen.getByRole('button', { name: '确认补货' }));

    await waitFor(() => {
      expect(screen.getByText('网络错误')).toBeInTheDocument();
    });
  });

  it('点击取消返回补货建议页', async () => {
    const user = userEvent.setup();
    renderOrderPage('/orders/new?store_id=S001&product_id=P0001&quantity=10');

    await waitForPageReady();
    const cancelBtn = screen.getByRole('button', { name: '取消' });
    await user.click(cancelBtn);

    expect(screen.getByTestId('replenishment')).toBeInTheDocument();
  });
});

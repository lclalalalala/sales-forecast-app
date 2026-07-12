/**
 * 补货下单表单 - OrderForm
 * ========================
 * 从补货建议或独立下单页调用，支持嵌入 Dialog 或作为页面主体。
 */

import { useEffect, useMemo, useState } from 'react';
import {
  ClipboardCheck, Package, Store as StoreIcon,
  CalendarDays, ShieldAlert, Calculator, Boxes, Tag, AlertTriangle,
} from 'lucide-react';
import { api } from '@/services/api';
import { isAbortError, getErrorMessage } from '@/lib/errors';
import { DEFAULT_TIME_RANGE } from '@/lib/constants';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import InventoryStatusBadge from '@/components/InventoryStatusBadge';
import type { Store, OrderDraft, ProductDetail } from '@/types';
import { cn } from '@/lib/utils';
import { formatInt as fmt, formatDecimal, formatLocalDate } from '@/lib/format';

const f1 = (n?: number | null) => formatDecimal(n, 1);

function parseQuantity(value: string | null): number {
  if (!value) return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 && Number.isInteger(parsed) ? parsed : -1;
}

function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

export interface OrderFormProps {
  storeId: string;
  productId: string;
  suggestedQuantity?: number;
  onClose: () => void;
  onViewDashboard?: () => void;
}

export default function OrderForm({
  storeId: initialStoreId,
  productId,
  suggestedQuantity,
  onClose,
  onViewDashboard,
}: OrderFormProps) {
  const [stores, setStores] = useState<Store[]>([]);
  const [storeId, setStoreId] = useState(initialStoreId);
  const [quantity, setQuantity] = useState<number | ''>(
    typeof suggestedQuantity === 'number' && suggestedQuantity >= 0 ? suggestedQuantity : '',
  );
  const [arrivalDate, setArrivalDate] = useState<Date | undefined>(undefined);
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<{ orderId: string } | null>(null);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState<ProductDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(true);

  const defaultArrivalDate = useMemo(() => {
    if (!detail) return undefined;
    return addDays(new Date(), Math.max(1, detail.replenishment.lead_time_k));
  }, [detail]);

  const effectiveArrivalDate = arrivalDate ?? defaultArrivalDate;

  useEffect(() => {
    const controller = new AbortController();
    api
      .getStores(controller.signal)
      .then(setStores)
      .catch((e: unknown) => {
        if (!isAbortError(e)) {
          setError(getErrorMessage(e, '门店列表加载失败，请刷新页面重试'));
        }
      });
    return () => controller.abort();
  }, []);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!storeId || !productId) {
      setDetailLoading(false);
      return;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    api
      .getProductDetail(productId, storeId, DEFAULT_TIME_RANGE, controller.signal)
      .then((res) => {
        setDetail(res.data);
      })
      .catch((e: unknown) => {
        if (!isAbortError(e)) {
          setError(getErrorMessage(e, '商品详情加载失败，请稍后重试'));
        }
      })
      .finally(() => setDetailLoading(false));
    return () => controller.abort();
  }, [storeId, productId]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const quantityNum = typeof quantity === 'number' ? quantity : 0;
  const quantityValid = quantity !== '';
  const canSubmit = storeId !== '' && productId !== '' && quantityValid && !loading && !detailLoading;

  const handleQuantityChange = (value: string) => {
    if (value === '') {
      setQuantity('');
      return;
    }
    const parsed = parseQuantity(value);
    if (parsed >= 0) {
      setQuantity(parsed);
    } else {
      setQuantity('');
    }
  };

  const handleSubmit = async (e: React.FormEvent, mode: 'draft' | 'confirm') => {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setError('');
    setSuccess(null);

    const draft: OrderDraft = {
      store_id: storeId,
      product_id: productId,
      quantity: quantityNum,
      expected_arrival_date: effectiveArrivalDate ? formatLocalDate(effectiveArrivalDate) : undefined,
      note: note.trim() || undefined,
    };

    try {
      const result = await api.submitOrder(draft);
      if (result.success) {
        setSuccess({ orderId: result.orderId });
      } else {
        setError(mode === 'draft' ? '保存草稿失败，请稍后重试' : '确认补货失败，请稍后重试');
      }
    } catch (e: unknown) {
      setError(getErrorMessage(e, '提交失败，请稍后重试'));
    } finally {
      setLoading(false);
    }
  };

  const basisText = detail
    ? `建议补货量 = ceil(max(0, 未来 ${detail.replenishment.lead_time_k} 天预测销量(${f1(detail.replenishment.forecast_k_total)}) + 安全库存(${fmt(detail.replenishment.safety_stock)}) - 当前库存(${fmt(detail.current_inventory)}) - 在途库存(${fmt(detail.in_transit_inventory)})))`
    : '';

  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-6">
      {success ? (
        <div className="text-center py-8">
          <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4 bg-[var(--status-sufficient-bg)]">
            <ClipboardCheck className="w-7 h-7 text-[var(--accent-secondary)]" />
          </div>
          <h3 className="text-lg font-semibold mb-1 text-[var(--text-primary)]">
            已生成补货记录
          </h3>
          <p className="text-sm mb-6 text-[var(--text-secondary)]">
            记录号：{success.orderId}
          </p>
          <div className="flex items-center justify-center gap-2 mb-6 px-3 py-2.5 rounded-lg border border-[var(--accent-warning)]/40 bg-[var(--accent-warning)]/10">
            <AlertTriangle className="w-4 h-4 shrink-0 text-[var(--accent-warning)]" />
            <p className="text-xs font-medium text-[var(--accent-warning)]">
              当前为前端演示，未向真实供应链系统提交采购订单。
            </p>
          </div>
          <div className="flex items-center justify-center gap-3">
            <Button variant="outline" onClick={onClose}>
              返回补货建议
            </Button>
            {onViewDashboard && (
              <Button onClick={onViewDashboard}>
                查看数据概览
              </Button>
            )}
          </div>
        </div>
      ) : (
        <form className="space-y-5" onSubmit={(e) => handleSubmit(e, 'confirm')}>
          <div className="space-y-1.5">
            <Label htmlFor="store" className="flex items-center gap-1.5">
              <StoreIcon className="w-3.5 h-3.5" />
              门店
            </Label>
            <Select value={storeId} onValueChange={setStoreId} disabled={stores.length === 0}>
              <SelectTrigger id="store" className="w-full bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-primary)]">
                <SelectValue placeholder="选择门店" />
              </SelectTrigger>
              <SelectContent className="bg-[var(--bg-surface)] border-[var(--border-subtle)]">
                {stores.map((s) => (
                  <SelectItem key={s.id} value={s.id} className="text-sm">
                    {s.name} ({s.id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <Label htmlFor="product" className="flex items-center gap-1.5">
                <Package className="w-3.5 h-3.5" />
                商品 ID
              </Label>
              <Input
                id="product"
                value={productId}
                readOnly
                className="bg-[var(--bg-surface-hover)] border-[var(--border-subtle)] text-[var(--text-primary)]"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="category" className="flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5" />
                商品类别
              </Label>
              <Input
                id="category"
                value={detail?.category || '-'}
                readOnly
                className="bg-[var(--bg-surface-hover)] border-[var(--border-subtle)] text-[var(--text-primary)]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <Label htmlFor="current_inventory" className="flex items-center gap-1.5">
                <Boxes className="w-3.5 h-3.5" />
                当前库存
              </Label>
              <Input
                id="current_inventory"
                value={detail ? `${fmt(detail.current_inventory)} 件` : '-'}
                readOnly
                className="bg-[var(--bg-surface-hover)] border-[var(--border-subtle)] text-[var(--text-primary)]"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="suggested" className="flex items-center gap-1.5">
                <Calculator className="w-3.5 h-3.5" />
                系统建议补货量
              </Label>
              <Input
                id="suggested"
                value={detail ? `${fmt(detail.replenishment.suggested_replenishment)} 件` : '-'}
                readOnly
                className="bg-[var(--bg-surface-hover)] border-[var(--border-subtle)] text-[var(--text-primary)]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <Label htmlFor="quantity" className="flex items-center gap-1.5">
                <Boxes className="w-3.5 h-3.5" />
                补货数量
              </Label>
              <Input
                id="quantity"
                type="number"
                min={0}
                step={1}
                value={quantity}
                onChange={(e) => handleQuantityChange(e.target.value)}
                required
                className="bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-primary)]"
              />
              <p className="text-xs text-[var(--text-tertiary)]">
                请输入非负整数
              </p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="arrival" className="flex items-center gap-1.5">
                <CalendarDays className="w-3.5 h-3.5" />
                预计到货日期
              </Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    id="arrival"
                    variant="outline"
                    className={cn(
                      'w-full justify-start text-left font-normal bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-primary)]',
                      !effectiveArrivalDate && 'text-[var(--text-tertiary)]',
                    )}
                  >
                    <CalendarDays className="mr-2 h-4 w-4" />
                    {effectiveArrivalDate ? formatLocalDate(effectiveArrivalDate) : '选择日期'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0 bg-[var(--bg-surface)] border-[var(--border-subtle)]">
                  <Calendar
                    mode="single"
                    selected={effectiveArrivalDate}
                    onSelect={setArrivalDate}
                    disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <Label className="flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5" />
                当前库存状态
              </Label>
              <div className="h-9 flex items-center px-3 rounded-md border border-[var(--border-subtle)] bg-[var(--bg-surface-hover)]">
                {detail ? (
                  <InventoryStatusBadge status={detail.replenishment.inventory_status} />
                ) : (
                  <span className="text-sm text-[var(--text-tertiary)]">-</span>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="flex items-center gap-1.5">
                <Calculator className="w-3.5 h-3.5" />
                补货依据
              </Label>
              <div className="min-h-[36px] flex items-center px-3 rounded-md border border-[var(--border-subtle)] bg-[var(--bg-surface-hover)]">
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  {basisText || '加载中...'}
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="note">备注</Label>
            <Input
              id="note"
              placeholder="选填：补充说明"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-primary)]"
            />
          </div>

          {error && (
            <div className="text-sm rounded-lg px-3 py-2 bg-[var(--status-critical-bg)] text-[var(--accent-error)]">
              {error}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              取消
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={!canSubmit || loading}
              onClick={(e) => handleSubmit(e, 'draft')}
            >
              {loading ? '保存中...' : '保存补货草稿'}
            </Button>
            <Button
              type="submit"
              disabled={!canSubmit || loading}
            >
              {loading ? '提交中...' : '确认补货'}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}

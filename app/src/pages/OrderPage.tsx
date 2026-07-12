/**
 * 补货下单详情页 - OrderPage
 * ==========================
 * 作为独立页面渲染补货表单；表格行内的“去下单”改为弹层调用同一 OrderForm。
 */

import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { ClipboardCheck, ArrowLeft } from 'lucide-react';
import OrderForm from '@/components/OrderForm';
import { useAnalysis } from '@/state/analysisContext';
import { PARAM_STORE_ID, PARAM_PRODUCT_ID, PARAM_QUANTITY } from '@/lib/constants';

function parseQuantity(value: string | null): number {
  if (!value) return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 && Number.isInteger(parsed) ? parsed : -1;
}

export default function OrderPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { storeId: currentStoreId } = useAnalysis();

  const storeId = searchParams.get(PARAM_STORE_ID) || currentStoreId || '';
  const productId = searchParams.get(PARAM_PRODUCT_ID) || '';
  const suggestedQuantity = parseQuantity(searchParams.get(PARAM_QUANTITY));

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Link
            to="/replenishment"
            className="flex items-center gap-1 text-xs hover:underline text-[var(--text-tertiary)]"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            返回补货建议
          </Link>
        </div>
        <h2 className="text-2xl font-semibold flex items-center gap-2 text-[var(--text-primary)]">
          <ClipboardCheck className="w-6 h-6 text-[var(--accent-primary)]" />
          补货下单
        </h2>
        <p className="text-sm mt-1 text-[var(--text-tertiary)]">
          请核对补货依据并填写数量与到货日期
        </p>
      </div>

      <div className="max-w-2xl">
        <OrderForm
          storeId={storeId}
          productId={productId}
          suggestedQuantity={suggestedQuantity >= 0 ? suggestedQuantity : undefined}
          onClose={() => navigate('/replenishment')}
          onViewDashboard={() => navigate('/')}
        />
      </div>
    </div>
  );
}

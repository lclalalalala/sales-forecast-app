/**
 * 应用入口 - App.tsx
 * ==================
 * 配置路由和全局布局。
 *
 * 路由配置:
 *   /              → 数据概览页 (DashboardPage)
 *   /rankings      → 排名页 (RankingPage)
 *   /replenishment → 补货建议页 (ReplenishmentPage)
 *   /orders/new    → 下单页 (OrderPage)
 *   /products/:id  → 商品详情页 (ProductDetailPage)
 *   /help          → 帮助文档 (HelpPage)
 *   /tech-doc      → 技术架构文档 (TechnicalDocPage)
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import DashboardPage from '@/pages/DashboardPage';
import ReplenishmentPage from '@/pages/ReplenishmentPage';
import ProductDetailPage from '@/pages/ProductDetailPage';
import OrderPage from '@/pages/OrderPage';
import HelpPage from '@/pages/HelpPage';
import RankingPage from '@/pages/RankingPage';
import TechnicalDocPage from '@/pages/TechnicalDocPage';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/rankings" element={<RankingPage />} />
        <Route path="/replenishment" element={<ReplenishmentPage />} />
        <Route path="/orders/new" element={<OrderPage />} />
        <Route path="/products/:productId" element={<ProductDetailPage />} />
        <Route path="/help" element={<HelpPage />} />
        <Route path="/tech-doc" element={<TechnicalDocPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;

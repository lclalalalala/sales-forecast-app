/**
 * 应用入口 - App.tsx
 * ==================
 * 配置路由和全局布局。
 * 
 * 路由配置:
 *   /              → 数据概览页 (DashboardPage)
 *   /replenishment → 补货建议页 (ReplenishmentPage)
 *   /product       → 商品详情页 (ProductDetailPage)
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import DashboardPage from '@/pages/DashboardPage';
import ReplenishmentPage from '@/pages/ReplenishmentPage';
import ProductDetailPage from '@/pages/ProductDetailPage';

function App() {
  return (
    <Layout>
      <Routes>
        {/* 数据概览页 - 默认首页 */}
        <Route path="/" element={<DashboardPage />} />

        {/* 补货建议页 */}
        <Route path="/replenishment" element={<ReplenishmentPage />} />

        {/* 商品详情页 */}
        <Route path="/product" element={<ProductDetailPage />} />

        {/* 未知路径重定向到首页 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;

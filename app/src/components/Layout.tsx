import { Link, useLocation } from 'react-router-dom';
import { BarChart3, Package, TrendingUp, Store } from 'lucide-react';
import type { ReactNode } from 'react';
import ThemeToggle from '@/components/ThemeToggle';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', label: '数据概览', icon: BarChart3 },
  { path: '/replenishment', label: '补货建议', icon: Package },
  { path: '/product', label: '商品详情', icon: TrendingUp },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* 导航栏 */}
      <nav
        className="sticky top-0 z-50"
        style={{
          backgroundColor: 'var(--card-surface)',
          borderBottom: '1px solid var(--border-color)',
          height: '56px',
        }}
      >
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-lg"
              style={{ backgroundColor: 'var(--status-normal-bg)' }}
            >
              <Store className="w-5 h-5" style={{ color: 'var(--accent-primary)' }} />
            </div>
            <h1
              className="text-base font-semibold hidden sm:block"
              style={{ color: 'var(--text-primary)' }}
            >
              零售门店库存与需求预测
            </h1>
          </div>

          {/* 导航链接 */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  /* group = Trigger: 承载 hover 状态 */
                  className={`
                    group flex items-center gap-2 px-4 py-2 rounded-lg
                    text-sm font-medium transition-all duration-200
                    ${isActive ? 'text-[var(--accent-primary)] bg-[var(--status-normal-bg)]' : 'text-[var(--text-secondary)]'}
                  `}
                >
                  {/* Target: 图标在 group-hover 时响应 */}
                  <item.icon className="w-4 h-4 transition-transform group-hover:scale-110" />
                  {/* Target: 文字在 group-hover 时响应 */}
                  <span className="hidden md:inline transition-colors group-hover:text-[var(--text-primary)]">
                    {item.label}
                  </span>
                </Link>
              );
            })}
            <div className="w-px h-5 mx-2 bg-[var(--border-subtle)]" />
            <ThemeToggle />
          </div>
        </div>
      </nav>

      {/* 主内容区域 */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {children}
      </main>
    </div>
  );
}

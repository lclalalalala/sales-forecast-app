/**
 * Layout 全局布局
 * ===============
 * 顶部导航、帮助入口、移动端抽屉导航、主题切换。
 */

import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  BarChart3, Package, TrendingUp, Store, Menu, HelpCircle, X,
} from 'lucide-react';
import type { ReactNode } from 'react';
import ThemeToggle from '@/components/ThemeToggle';
import HelpDrawer from '@/components/HelpDrawer';
import { DEFAULT_PRODUCT_ID } from '@/lib/constants';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';

const HELP_TIP_KEY = 'sephora-help-tip-dismissed';

const navItems = [
  { path: '/', label: '数据概览', icon: BarChart3 },
  { path: '/replenishment', label: '补货建议', icon: Package },
  { path: `/products/${DEFAULT_PRODUCT_ID}`, label: '商品分析', icon: TrendingUp },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === `/products/${DEFAULT_PRODUCT_ID}`) {
      return location.pathname.startsWith('/products');
    }
    return location.pathname === path;
  };

  return (
    <>
      {navItems.map((item) => {
        const active = isActive(item.path);
        const to = item.path;
        return (
          <Link
            key={item.path}
            to={to}
            onClick={onNavigate}
            className={`
              group flex items-center gap-2 px-4 py-2 rounded-lg
              text-sm font-medium transition-colors duration-200
              ${active ? 'text-[var(--accent-primary)] bg-[var(--bg-surface-hover)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)]'}
            `}
          >
            <item.icon className="w-4 h-4 transition-transform group-hover:scale-110" />
            <span className="transition-colors">{item.label}</span>
          </Link>
        );
      })}
    </>
  );
}

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [showHelpTip, setShowHelpTip] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(HELP_TIP_KEY)) {
      const timer = setTimeout(() => setShowHelpTip(true), 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const dismissTip = () => {
    setShowHelpTip(false);
    localStorage.setItem(HELP_TIP_KEY, '1');
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <nav
        className="sticky top-0 z-50 h-14 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)]"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[var(--bg-surface-hover)]">
              <Store className="w-5 h-5 text-[var(--accent-primary)]" />
            </div>
            <h1 className="text-base font-semibold hidden sm:block text-[var(--text-primary)]">
              零售门店库存与需求预测
            </h1>
          </div>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            <NavLinks />
            <div className="w-px h-5 mx-2 bg-[var(--border-subtle)]" />
            <div className="relative">
              <HelpDrawer>
                <Button variant="ghost" size="sm" aria-label="帮助文档" className="gap-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)]" onClick={dismissTip}>
                  <HelpCircle className="w-4 h-4" />
                  <span className="text-xs">帮助文档</span>
                </Button>
              </HelpDrawer>
              {showHelpTip && (
                <div className="absolute top-full right-0 mt-2 z-50 animate-in fade-in slide-in-from-top-2 duration-300">
                  <div className="relative bg-[var(--accent-primary)] text-white text-xs rounded-lg px-3 py-2 shadow-lg whitespace-nowrap">
                    <button
                      type="button"
                      onClick={dismissTip}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-white text-[var(--accent-primary)] flex items-center justify-center shadow-sm"
                    >
                      <X className="w-3 h-3" />
                    </button>
                    👋 首次使用？点击查看补货说明
                    <div className="absolute -top-1 right-4 w-2 h-2 bg-[var(--accent-primary)] rotate-45" />
                  </div>
                </div>
              )}
            </div>
            <ThemeToggle />
          </div>

          {/* Mobile nav */}
          <div className="flex md:hidden items-center gap-1">
            <HelpDrawer>
              <Button variant="ghost" size="icon" aria-label="帮助说明" className="text-[var(--text-secondary)]">
                <HelpCircle className="w-5 h-5" />
              </Button>
            </HelpDrawer>
            <ThemeToggle />
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="打开导航" className="text-[var(--text-secondary)]">
                  <Menu className="w-5 h-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[260px] bg-[var(--bg-surface)] border-[var(--border-subtle)]">
                <SheetHeader className="pb-4 border-b border-[var(--border-subtle)]">
                  <SheetTitle className="flex items-center gap-2 text-[var(--text-primary)]">
                    <Store className="w-5 h-5 text-[var(--accent-primary)]" />
                    导航
                  </SheetTitle>
                </SheetHeader>
                <div className="mt-4 flex flex-col gap-1">
                  <NavLinks />
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>
    </div>
  );
}

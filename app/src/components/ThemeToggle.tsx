/**
 * ThemeToggle 主题切换
 * ====================
 * 支持 light / dark / system 三种模式。
 */

import { useTheme } from 'next-themes';
import { Sun, Moon, Monitor, Check } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

type ThemeOption = {
  value: 'light' | 'dark' | 'system';
  label: string;
  icon: React.ComponentType<{ className?: string }>;
};

const themeOptions: ThemeOption[] = [
  { value: 'light', label: '浅色', icon: Sun },
  { value: 'dark', label: '深色', icon: Moon },
  { value: 'system', label: '跟随系统', icon: Monitor },
];

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const currentTheme = (theme as ThemeOption['value']) || 'system';

  const activeOption = themeOptions.find((t) => t.value === currentTheme) || themeOptions[2];
  const ActiveIcon = activeOption.icon;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="切换主题"
          title="切换主题"
          className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)]"
        >
          <ActiveIcon className="w-5 h-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="min-w-[140px] bg-[var(--bg-surface)] border-[var(--border-subtle)]"
      >
        {themeOptions.map((option) => {
          const Icon = option.icon;
          const isActive = currentTheme === option.value;
          return (
            <DropdownMenuItem
              key={option.value}
              onClick={() => setTheme(option.value)}
              className="flex items-center justify-between gap-2 text-sm text-[var(--text-primary)] focus:bg-[var(--bg-surface-hover)]"
            >
              <div className="flex items-center gap-2">
                <Icon className="w-4 h-4" />
                {option.label}
              </div>
              {isActive && <Check className="w-4 h-4 text-[var(--accent-primary)]" />}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

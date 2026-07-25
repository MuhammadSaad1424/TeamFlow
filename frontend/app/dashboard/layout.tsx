'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuthStore } from '@/lib/store';

const navItems = [
  { href: '/dashboard', label: 'Overview', icon: '📊' },
  { href: '/dashboard/repositories', label: 'Repositories', icon: '📁' },
  { href: '/dashboard/chat', label: 'AI Chat', icon: '💬' },
  { href: '/dashboard/architecture', label: 'Architecture', icon: '🏗️' },
  { href: '/dashboard/docs', label: 'Documentation', icon: '📝' },
  { href: '/dashboard/analytics', label: 'Analytics', icon: '📈' },
  { href: '/dashboard/settings', label: 'Settings', icon: '⚙️' },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuthStore();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <div className="flex min-h-screen">
      <aside className="fixed left-0 top-0 z-40 flex h-full w-64 flex-col border-r border-white/10 bg-[hsl(var(--card))]">
        <div className="flex items-center gap-2 border-b border-white/10 px-6 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500 text-sm font-bold">
            TF
          </div>
          <span className="font-semibold">TeamFlow AI</span>
        </div>

        <nav className="flex-1 space-y-1 p-4">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                  active
                    ? 'bg-primary-500/20 text-primary-500'
                    : 'text-[hsl(var(--muted-foreground))] hover:bg-white/5 hover:text-white'
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-white/10 p-4">
          <div className="mb-3 flex items-center gap-3">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="h-8 w-8 rounded-full" />
            ) : (
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-500/20 text-xs">
                {user?.github_username?.[0]?.toUpperCase() || 'U'}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{user?.display_name || user?.github_username}</p>
              <p className="truncate text-xs text-[hsl(var(--muted-foreground))]">{user?.subscription_tier}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="btn-secondary w-full text-xs">
            Sign Out
          </button>
        </div>
      </aside>

      <main className="ml-64 flex-1 p-8">{children}</main>
    </div>
  );
}

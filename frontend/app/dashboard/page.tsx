'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_repositories: 0,
    total_queries: 0,
    avg_confidence_score: 0,
    avg_query_time_ms: 0,
  });
  const [usage, setUsage] = useState({ used_today: 0, daily_limit: 100, remaining: 100 });

  useEffect(() => {
    api.getDashboard().then((res) => {
      if (res.success && res.data) setStats(res.data as typeof stats);
    });
    api.getUsage().then((res) => {
      if (res.success && res.data) setUsage(res.data as typeof usage);
    });
  }, []);

  const cards = [
    { label: 'Repositories', value: stats.total_repositories, href: '/dashboard/repositories' },
    { label: 'Total Queries', value: stats.total_queries, href: '/dashboard/chat' },
    { label: 'Avg Confidence', value: `${(stats.avg_confidence_score * 100).toFixed(0)}%`, href: '/dashboard/analytics' },
    { label: 'Avg Response Time', value: `${stats.avg_query_time_ms.toFixed(0)}ms`, href: '/dashboard/analytics' },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-[hsl(var(--muted-foreground))]">
          Welcome back! Here&apos;s an overview of your codebase intelligence activity.
        </p>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <Link key={card.label} href={card.href} className="card hover:border-primary-500/30 transition">
            <p className="text-sm text-[hsl(var(--muted-foreground))]">{card.label}</p>
            <p className="mt-1 text-3xl font-bold">{card.value}</p>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
          <div className="space-y-3">
            <Link href="/dashboard/repositories" className="btn-primary w-full">
              Add Repository
            </Link>
            <Link href="/dashboard/chat" className="btn-secondary w-full">
              Start AI Chat
            </Link>
            <Link href="/dashboard/docs" className="btn-secondary w-full">
              Generate Documentation
            </Link>
          </div>
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Usage Today</h2>
          <div className="mb-2 flex justify-between text-sm">
            <span>{usage.used_today} queries used</span>
            <span>{usage.remaining} remaining</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-primary-500 transition-all"
              style={{ width: `${Math.min((usage.used_today / usage.daily_limit) * 100, 100)}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-[hsl(var(--muted-foreground))]">
            Daily limit: {usage.daily_limit} queries
          </p>
        </div>
      </div>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function AnalyticsPage() {
  const [dashboard, setDashboard] = useState({
    total_queries: 0,
    avg_query_time_ms: 0,
    avg_confidence_score: 0,
    total_repositories: 0,
    queries_by_day: [] as Array<{ date: string; count: number }>,
    top_questions: [] as Array<{ question: string; count: number }>,
    model_usage: {} as Record<string, number>,
  });

  useEffect(() => {
    api.getDashboard().then((res) => {
      if (res.success && res.data) setDashboard(res.data as typeof dashboard);
    });
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-[hsl(var(--muted-foreground))]">
          Track usage, performance, and query patterns
        </p>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-4">
        {[
          { label: 'Total Queries', value: dashboard.total_queries },
          { label: 'Repositories', value: dashboard.total_repositories },
          { label: 'Avg Confidence', value: `${(dashboard.avg_confidence_score * 100).toFixed(0)}%` },
          { label: 'Avg Response', value: `${dashboard.avg_query_time_ms.toFixed(0)}ms` },
        ].map((s) => (
          <div key={s.label} className="card">
            <p className="text-sm text-[hsl(var(--muted-foreground))]">{s.label}</p>
            <p className="mt-1 text-3xl font-bold">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Queries (Last 7 Days)</h2>
          {dashboard.queries_by_day.length === 0 ? (
            <p className="text-sm text-[hsl(var(--muted-foreground))]">No query data yet</p>
          ) : (
            <div className="space-y-2">
              {dashboard.queries_by_day.map((d) => (
                <div key={d.date} className="flex items-center gap-3">
                  <span className="w-24 text-xs text-[hsl(var(--muted-foreground))]">{d.date}</span>
                  <div className="flex-1 h-4 overflow-hidden rounded bg-white/10">
                    <div
                      className="h-full rounded bg-primary-500"
                      style={{
                        width: `${Math.min((d.count / Math.max(...dashboard.queries_by_day.map((x) => x.count), 1)) * 100, 100)}%`,
                      }}
                    />
                  </div>
                  <span className="w-8 text-xs text-right">{d.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Top Questions</h2>
          {dashboard.top_questions.length === 0 ? (
            <p className="text-sm text-[hsl(var(--muted-foreground))]">No questions yet</p>
          ) : (
            <ul className="space-y-3">
              {dashboard.top_questions.map((q, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-500/20 text-xs">
                    {i + 1}
                  </span>
                  <div>
                    <p>{q.question}</p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">{q.count} times</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

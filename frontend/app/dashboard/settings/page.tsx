'use client';

import { useAuthStore } from '@/lib/store';

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-[hsl(var(--muted-foreground))]">
          Manage your account and preferences
        </p>
      </div>

      <div className="space-y-6 max-w-2xl">
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Profile</h2>
          <div className="flex items-center gap-4 mb-6">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="h-16 w-16 rounded-full" />
            ) : (
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-500/20 text-2xl">
                {user?.github_username?.[0]?.toUpperCase()}
              </div>
            )}
            <div>
              <p className="font-semibold">{user?.display_name || user?.github_username}</p>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">{user?.email}</p>
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-white/5 pb-2">
              <span className="text-[hsl(var(--muted-foreground))]">GitHub Username</span>
              <span>{user?.github_username}</span>
            </div>
            <div className="flex justify-between border-b border-white/5 pb-2">
              <span className="text-[hsl(var(--muted-foreground))]">Subscription</span>
              <span className="capitalize">{user?.subscription_tier}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">API Configuration</h2>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Backend URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}
          </p>
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">About</h2>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            TeamFlow AI v1.0.0 — Intelligent Codebase Understanding System.
            Built with Next.js, FastAPI, LangChain, and RAG pipeline.
          </p>
        </div>
      </div>
    </div>
  );
}

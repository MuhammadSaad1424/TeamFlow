'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const handleDevLogin = async () => {
    setLoading(true);
    try {
      const res = await api.devLogin();
      if (res.success && res.data) {
        const data = res.data as {
          access_token: string;
          refresh_token: string;
          user: Parameters<typeof setAuth>[0];
        };
        setAuth(data.user, data.access_token, data.refresh_token);
        toast.success('Welcome to TeamFlow AI!');
        router.push('/dashboard');
      } else {
        toast.error(res.message || 'Login failed');
      }
    } catch {
      toast.error('Could not connect to backend. Is the server running?');
    } finally {
      setLoading(false);
    }
  };

  const handleGitHubLogin = () => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/github`;
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500 font-bold">
              TF
            </div>
            <span className="text-xl font-semibold">TeamFlow AI</span>
          </Link>
          <p className="mt-4 text-[hsl(var(--muted-foreground))]">
            Sign in to access your codebase intelligence dashboard
          </p>
        </div>

        <div className="card space-y-4">
          <button
            onClick={handleGitHubLogin}
            className="flex w-full items-center justify-center gap-3 rounded-lg bg-white px-4 py-3 text-sm font-medium text-gray-900 transition hover:bg-gray-100"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.395-.135-.345-.72-1.395-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            Continue with GitHub
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-[hsl(var(--card))] px-2 text-[hsl(var(--muted-foreground))]">
                or for development
              </span>
            </div>
          </div>

          <button
            onClick={handleDevLogin}
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Signing in...' : 'Dev Login (No GitHub)'}
          </button>
        </div>

        <p className="mt-6 text-center text-xs text-[hsl(var(--muted-foreground))]">
          By signing in, you agree to our terms of service and privacy policy.
        </p>
      </div>
    </div>
  );
}

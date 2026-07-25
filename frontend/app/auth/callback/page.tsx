'use client';

import { Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setAuth = useAuthStore((s) => s.setAuth);

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const userId = searchParams.get('user_id');

    if (accessToken && refreshToken && userId) {
      setAuth(
        {
          id: userId,
          github_username: searchParams.get('username') || '',
          email: searchParams.get('email') || '',
          avatar_url: searchParams.get('avatar_url') || undefined,
          display_name: searchParams.get('username') || undefined,
          subscription_tier: 'free',
        },
        accessToken,
        refreshToken,
      );
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [searchParams, setAuth, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-[hsl(var(--muted-foreground))]">Completing sign in...</p>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-[hsl(var(--muted-foreground))]">Loading...</p>
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}

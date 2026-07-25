const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface ApiResponse<T = unknown> {
  success: boolean;
  statusCode: number;
  message?: string;
  data?: T;
  error?: unknown;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  return res.json();
}

export const api = {
  devLogin: () => request('/auth/dev-login', { method: 'POST' }),

  getMe: () => request('/auth/me'),

  logout: () => request('/auth/logout', { method: 'POST' }),

  getRepositories: (page = 1) => request(`/repositories?page=${page}&limit=20`),

  createRepository: (github_url: string) =>
    request('/repositories', {
      method: 'POST',
      body: JSON.stringify({ github_url }),
    }),

  deleteRepository: (id: string) =>
    request(`/repositories/${id}`, { method: 'DELETE' }),

  indexRepository: (id: string) =>
    request(`/repositories/${id}/index`, { method: 'POST' }),

  getIndexStatus: (id: string) => request(`/repositories/${id}/index/status`),

  sendChat: (data: {
    repository_id: string;
    query: string;
    conversation_id?: string;
    context_limit?: number;
  }) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getChatHistory: (repositoryId?: string) =>
    request(`/chat/history${repositoryId ? `?repository_id=${repositoryId}` : ''}`),

  getConversation: (id: string) => request(`/chat/${id}`),

  getDashboard: () => request('/analytics/dashboard'),

  getUsage: () => request('/analytics/usage'),

  getArchitecture: (repoId: string) => request(`/architecture/${repoId}`),

  getDependencies: (repoId: string) => request(`/architecture/${repoId}/dependencies`),

  generateDocs: (repoId: string, docType: string) =>
    request(`/documentation/${repoId}/generate?doc_type=${docType}`, { method: 'POST' }),
};

export type { ApiResponse };

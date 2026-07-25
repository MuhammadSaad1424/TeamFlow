'use client';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { useAppStore } from '@/lib/store';

interface Repository {
  id: string;
  repo_name: string;
  repo_url: string;
  language_primary: string | null;
  indexing_status: string;
  file_count: number;
  embedding_count: number;
  created_at: string;
}

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const setSelectedRepository = useAppStore((s) => s.setSelectedRepository);

  const loadRepos = async () => {
    const res = await api.getRepositories();
    if (res.success && res.data) {
      const data = res.data as { items: Repository[] };
      setRepos(data.items || []);
    }
  };

  useEffect(() => {
    loadRepos();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    try {
      const res = await api.createRepository(url.trim());
      if (res.success) {
        toast.success('Repository added!');
        setUrl('');
        loadRepos();
      } else {
        toast.error(res.message || 'Failed to add repository');
      }
    } catch {
      toast.error('Connection error');
    } finally {
      setLoading(false);
    }
  };

  const handleIndex = async (id: string) => {
    toast.loading('Starting indexing...', { id: 'index' });
    const res = await api.indexRepository(id);
    toast.dismiss('index');
    if (res.success) {
      toast.success('Indexing started! This may take a few minutes.');
      pollStatus(id);
    } else {
      toast.error(res.message || 'Indexing failed');
    }
  };

  const pollStatus = (id: string) => {
    const interval = setInterval(async () => {
      const res = await api.getIndexStatus(id);
      if (res.success && res.data) {
        const status = (res.data as { status: string }).status;
        if (status === 'completed' || status === 'failed') {
          clearInterval(interval);
          loadRepos();
          toast.success(status === 'completed' ? 'Indexing complete!' : 'Indexing failed');
        }
      }
    }, 5000);
    setTimeout(() => clearInterval(interval), 300000);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this repository?')) return;
    const res = await api.deleteRepository(id);
    if (res.success) {
      toast.success('Repository deleted');
      loadRepos();
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'in_progress': return 'text-yellow-400';
      case 'failed': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Repositories</h1>
        <p className="text-[hsl(var(--muted-foreground))]">
          Connect GitHub repositories for AI-powered analysis
        </p>
      </div>

      <form onSubmit={handleAdd} className="card mb-8 flex gap-4">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/owner/repository"
          className="input flex-1"
          required
        />
        <button type="submit" disabled={loading} className="btn-primary whitespace-nowrap">
          {loading ? 'Adding...' : 'Add Repository'}
        </button>
      </form>

      {repos.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-[hsl(var(--muted-foreground))]">No repositories yet. Add one above to get started.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {repos.map((repo) => (
            <div key={repo.id} className="card flex flex-wrap items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold">{repo.repo_name}</h3>
                <a href={repo.repo_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary-500 hover:underline">
                  {repo.repo_url}
                </a>
                <div className="mt-2 flex flex-wrap gap-4 text-xs text-[hsl(var(--muted-foreground))]">
                  <span className={statusColor(repo.indexing_status)}>
                    ● {repo.indexing_status}
                  </span>
                  {repo.language_primary && <span>{repo.language_primary}</span>}
                  <span>{repo.file_count} files</span>
                  <span>{repo.embedding_count} embeddings</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedRepository(repo.id)}
                  className="btn-secondary text-xs"
                >
                  Select
                </button>
                {repo.indexing_status !== 'in_progress' && (
                  <button onClick={() => handleIndex(repo.id)} className="btn-primary text-xs">
                    {repo.indexing_status === 'completed' ? 'Re-index' : 'Index'}
                  </button>
                )}
                <button onClick={() => handleDelete(repo.id)} className="btn-secondary text-xs text-red-400">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

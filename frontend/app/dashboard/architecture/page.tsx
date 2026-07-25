'use client';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { useAppStore } from '@/lib/store';

interface Repository {
  id: string;
  repo_name: string;
  indexing_status: string;
}

export default function ArchitecturePage() {
  const selectedRepoId = useAppStore((s) => s.selectedRepositoryId);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [repoId, setRepoId] = useState(selectedRepoId || '');
  const [architecture, setArchitecture] = useState<Record<string, unknown> | null>(null);
  const [dependencies, setDependencies] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getRepositories().then((res) => {
      if (res.success && res.data) {
        const items = (res.data as { items: Repository[] }).items || [];
        setRepos(items.filter((r) => r.indexing_status === 'completed'));
        if (!repoId && items.length > 0) {
          const c = items.find((r) => r.indexing_status === 'completed');
          if (c) setRepoId(c.id);
        }
      }
    });
  }, [repoId]);

  const loadAnalysis = async () => {
    if (!repoId) return;
    setLoading(true);
    try {
      const [archRes, depRes] = await Promise.all([
        api.getArchitecture(repoId),
        api.getDependencies(repoId),
      ]);
      if (archRes.success) setArchitecture(archRes.data as Record<string, unknown>);
      if (depRes.success) setDependencies(depRes.data as Record<string, unknown>);
    } catch {
      toast.error('Failed to load architecture');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (repoId) loadAnalysis();
  }, [repoId]);

  const modules = (architecture?.modules as Array<{ name: string; files: number; lines: number; functions: number }>) || [];
  const externalDeps = (dependencies?.external_dependencies as string[]) || [];

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Architecture Explorer</h1>
          <p className="text-[hsl(var(--muted-foreground))]">
            Understand module structure and dependencies
          </p>
        </div>
        <select value={repoId} onChange={(e) => setRepoId(e.target.value)} className="input w-64">
          <option value="">Select repository...</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>{r.repo_name}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="card text-center py-12">Loading analysis...</div>
      ) : architecture ? (
        <div className="space-y-6">
          <div className="card">
            <h2 className="mb-2 text-lg font-semibold">Summary</h2>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">
              {(architecture.summary as string) || 'No summary available'}
            </p>
            <div className="mt-4 flex gap-6 text-sm">
              <span>{architecture.total_files as number} files</span>
              <span>{architecture.total_loc as number} lines of code</span>
              <span>{(architecture.languages as string[])?.join(', ')}</span>
            </div>
          </div>

          <div className="card">
            <h2 className="mb-4 text-lg font-semibold">Modules</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-left text-[hsl(var(--muted-foreground))]">
                    <th className="pb-2">Module</th>
                    <th className="pb-2">Files</th>
                    <th className="pb-2">Lines</th>
                    <th className="pb-2">Functions</th>
                  </tr>
                </thead>
                <tbody>
                  {modules.map((m) => (
                    <tr key={m.name} className="border-b border-white/5">
                      <td className="py-2 font-mono">{m.name}</td>
                      <td className="py-2">{m.files}</td>
                      <td className="py-2">{m.lines}</td>
                      <td className="py-2">{m.functions}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {architecture.data_flow_diagram && (
            <div className="card">
              <h2 className="mb-4 text-lg font-semibold">Data Flow</h2>
              <pre className="overflow-x-auto rounded-lg bg-black/30 p-4 text-xs font-mono">
                {architecture.data_flow_diagram as string}
              </pre>
            </div>
          )}

          {externalDeps.length > 0 && (
            <div className="card">
              <h2 className="mb-4 text-lg font-semibold">External Dependencies</h2>
              <div className="flex flex-wrap gap-2">
                {externalDeps.slice(0, 30).map((dep) => (
                  <span key={dep} className="rounded-full bg-white/5 px-3 py-1 text-xs font-mono">
                    {dep}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-[hsl(var(--muted-foreground))]">
            Select an indexed repository to view architecture
          </p>
        </div>
      )}
    </div>
  );
}

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

const DOC_TYPES = [
  { id: 'readme', label: 'README', description: 'Project overview and setup guide' },
  { id: 'api', label: 'API Documentation', description: 'Endpoint and interface docs' },
  { id: 'technical', label: 'Technical Docs', description: 'Architecture and implementation details' },
  { id: 'developer_guide', label: 'Developer Guide', description: 'Onboarding for new contributors' },
];

export default function DocsPage() {
  const selectedRepoId = useAppStore((s) => s.selectedRepositoryId);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [repoId, setRepoId] = useState(selectedRepoId || '');
  const [docType, setDocType] = useState('readme');
  const [content, setContent] = useState('');
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

  const handleGenerate = async () => {
    if (!repoId) {
      toast.error('Select a repository first');
      return;
    }
    setLoading(true);
    setContent('');
    toast.loading('Generating documentation...', { id: 'docs' });
    try {
      const res = await api.generateDocs(repoId, docType);
      toast.dismiss('docs');
      if (res.success && res.data) {
        setContent((res.data as { content: string }).content);
        toast.success('Documentation generated!');
      } else {
        toast.error(res.message || 'Generation failed');
      }
    } catch {
      toast.dismiss('docs');
      toast.error('Connection error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Documentation Generator</h1>
        <p className="text-[hsl(var(--muted-foreground))]">
          Auto-generate documentation from your indexed codebase
        </p>
      </div>

      <div className="mb-6 flex flex-wrap gap-4">
        <select value={repoId} onChange={(e) => setRepoId(e.target.value)} className="input w-64">
          <option value="">Select repository...</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>{r.repo_name}</option>
          ))}
        </select>
        <button onClick={handleGenerate} disabled={loading || !repoId} className="btn-primary">
          {loading ? 'Generating...' : 'Generate'}
        </button>
      </div>

      <div className="mb-6 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        {DOC_TYPES.map((dt) => (
          <button
            key={dt.id}
            onClick={() => setDocType(dt.id)}
            className={`card text-left transition ${
              docType === dt.id ? 'border-primary-500/50 bg-primary-500/10' : 'hover:border-white/20'
            }`}
          >
            <p className="font-medium">{dt.label}</p>
            <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">{dt.description}</p>
          </button>
        ))}
      </div>

      {content ? (
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              {DOC_TYPES.find((d) => d.id === docType)?.label}
            </h2>
            <button
              onClick={() => navigator.clipboard.writeText(content)}
              className="btn-secondary text-xs"
            >
              Copy
            </button>
          </div>
          <pre className="max-h-[600px] overflow-auto whitespace-pre-wrap text-sm leading-relaxed">
            {content}
          </pre>
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-[hsl(var(--muted-foreground))]">
            Select a doc type and click Generate to create documentation
          </p>
        </div>
      )}
    </div>
  );
}

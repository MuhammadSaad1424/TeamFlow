'use client';

import { useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { useAppStore } from '@/lib/store';

interface Message {
  id: string;
  query: string;
  response: string;
  confidence_score?: number;
  citations?: Array<{
    file_path: string;
    snippet: string;
    start_line: number;
    end_line: number;
    relevance_score: number;
  }>;
}

interface Repository {
  id: string;
  repo_name: string;
  indexing_status: string;
}

export default function ChatPage() {
  const selectedRepoId = useAppStore((s) => s.selectedRepositoryId);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [repoId, setRepoId] = useState(selectedRepoId || '');
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getRepositories().then((res) => {
      if (res.success && res.data) {
        const items = (res.data as { items: Repository[] }).items || [];
        setRepos(items.filter((r) => r.indexing_status === 'completed'));
        if (!repoId && items.length > 0) {
          const completed = items.find((r) => r.indexing_status === 'completed');
          if (completed) setRepoId(completed.id);
        }
      }
    });
  }, [repoId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !repoId) {
      if (!repoId) toast.error('Select an indexed repository first');
      return;
    }

    const userQuery = query.trim();
    setQuery('');
    setLoading(true);

    setMessages((prev) => [...prev, { id: Date.now().toString(), query: userQuery, response: '...' }]);

    try {
      const res = await api.sendChat({
        repository_id: repoId,
        query: userQuery,
        conversation_id: conversationId,
      });

      if (res.success && res.data) {
        const data = res.data as Message & { conversation_id: string };
        setConversationId(data.conversation_id);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            id: data.message_id as unknown as string,
            query: data.query,
            response: data.response,
            confidence_score: data.confidence_score,
            citations: data.citations,
          };
          return updated;
        });
      } else {
        toast.error(res.message || 'Query failed');
        setMessages((prev) => prev.slice(0, -1));
      }
    } catch {
      toast.error('Connection error');
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    'Where is authentication implemented?',
    'Explain the main architecture',
    'How does the database schema work?',
    'Find JWT token handling',
  ];

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI Code Chat</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Ask natural language questions about your codebase
          </p>
        </div>
        <select
          value={repoId}
          onChange={(e) => setRepoId(e.target.value)}
          className="input w-64"
        >
          <option value="">Select repository...</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>{r.repo_name}</option>
          ))}
        </select>
      </div>

      <div className="card flex-1 overflow-y-auto space-y-6 mb-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <p className="mb-6 text-[hsl(var(--muted-foreground))]">
              Select a repository and ask a question to get started
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => setQuery(s)}
                  className="rounded-full border border-white/10 px-4 py-2 text-sm hover:border-primary-500/50 transition"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className="space-y-3">
              <div className="flex justify-end">
                <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary-500/20 px-4 py-3">
                  <p className="text-sm">{msg.query}</p>
                </div>
              </div>
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl rounded-bl-sm bg-white/5 px-4 py-3">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.response}</p>
                  {msg.confidence_score !== undefined && (
                    <p className="mt-2 text-xs text-[hsl(var(--muted-foreground))]">
                      Confidence: {(msg.confidence_score * 100).toFixed(0)}%
                    </p>
                  )}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 space-y-2 border-t border-white/10 pt-3">
                      <p className="text-xs font-medium text-primary-500">Sources</p>
                      {msg.citations.map((c, j) => (
                        <div key={j} className="rounded-lg bg-black/20 p-2 text-xs">
                          <p className="font-mono text-primary-400">{c.file_path}:{c.start_line}-{c.end_line}</p>
                          <pre className="mt-1 overflow-x-auto text-[hsl(var(--muted-foreground))]">{c.snippet}</pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="flex gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about your codebase..."
          className="input flex-1"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !repoId} className="btn-primary px-6">
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

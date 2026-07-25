'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

const features = [
  {
    title: 'AI Code Chat',
    description: 'Ask natural language questions and get grounded answers with source citations.',
    icon: '💬',
  },
  {
    title: 'Repository Analysis',
    description: 'Connect GitHub repos, index code, detect languages, and map structure automatically.',
    icon: '🔍',
  },
  {
    title: 'Architecture Explorer',
    description: 'Visualize modules, dependencies, and data flow across your codebase.',
    icon: '🏗️',
  },
  {
    title: 'Documentation Generator',
    description: 'Auto-generate README, API docs, and developer guides from your source code.',
    icon: '📝',
  },
  {
    title: 'Hybrid RAG Search',
    description: 'Dense + BM25 retrieval with reranking for accurate context retrieval.',
    icon: '🧠',
  },
  {
    title: 'Analytics Dashboard',
    description: 'Track queries, confidence scores, and usage patterns over time.',
    icon: '📊',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <nav className="fixed top-0 z-50 w-full border-b border-white/10 bg-[hsl(var(--background))]/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500 text-sm font-bold">
              TF
            </div>
            <span className="text-lg font-semibold">TeamFlow AI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="btn-secondary">
              Sign In
            </Link>
            <Link href="/login" className="btn-primary">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <section className="relative overflow-hidden px-6 pb-24 pt-32">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-500/10 to-transparent" />
        <div className="relative mx-auto max-w-4xl text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <span className="mb-4 inline-block rounded-full border border-primary-500/30 bg-primary-500/10 px-4 py-1 text-sm text-primary-500">
              RAG-Powered Code Intelligence
            </span>
            <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight md:text-6xl">
              Understand Any Codebase
              <span className="block text-primary-500">With AI</span>
            </h1>
            <p className="mx-auto mb-10 max-w-2xl text-lg text-[hsl(var(--muted-foreground))]">
              TeamFlow AI connects to your GitHub repositories and lets you ask questions,
              explore architecture, trace dependencies, and generate documentation — all
              grounded in your actual source code.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/login" className="btn-primary px-8 py-3 text-base">
                Start Free →
              </Link>
              <a href="#features" className="btn-secondary px-8 py-3 text-base">
                Learn More
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="features" className="px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-4 text-center text-3xl font-bold">Everything You Need</h2>
          <p className="mb-16 text-center text-[hsl(var(--muted-foreground))]">
            A complete codebase intelligence platform for developers and teams
          </p>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="card hover:border-primary-500/30 transition"
              >
                <div className="mb-4 text-3xl">{f.icon}</div>
                <h3 className="mb-2 text-lg font-semibold">{f.title}</h3>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">{f.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/10 px-6 py-24">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="mb-4 text-3xl font-bold">Ready to explore your code?</h2>
          <p className="mb-8 text-[hsl(var(--muted-foreground))]">
            Connect a GitHub repository and start asking questions in minutes.
          </p>
          <Link href="/login" className="btn-primary px-8 py-3 text-base">
            Get Started Free
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/10 px-6 py-8 text-center text-sm text-[hsl(var(--muted-foreground))]">
        © 2026 TeamFlow AI — Final Year Project
      </footer>
    </div>
  );
}

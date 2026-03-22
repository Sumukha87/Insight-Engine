"use client";

import React, { useEffect, useRef, useState } from "react";
import { api, clearTokens, GraphPath, QueryResponse, SourceCitation } from "@/lib/api";

const DOMAIN_COLORS: Record<string, string> = {
  Aerospace:      "bg-blue-500/20 text-blue-300",
  Medical:        "bg-emerald-500/20 text-emerald-300",
  Materials:      "bg-amber-500/20 text-amber-300",
  Energy:         "bg-yellow-500/20 text-yellow-300",
  Biotechnology:  "bg-green-500/20 text-green-300",
  Robotics:       "bg-cyan-500/20 text-cyan-300",
  Quantum:        "bg-violet-500/20 text-violet-300",
  Nanotechnology: "bg-pink-500/20 text-pink-300",
  Environment:    "bg-teal-500/20 text-teal-300",
  Semiconductors: "bg-orange-500/20 text-orange-300",
  Pharma:         "bg-red-500/20 text-red-300",
  Neuroscience:   "bg-purple-500/20 text-purple-300",
};

function DomainBadge({ domain }: { domain: string }) {
  const cls = DOMAIN_COLORS[domain] ?? "bg-white/10 text-slate-300";
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {domain}
    </span>
  );
}

function CitationCard({ citation, index }: { citation: SourceCitation; index: number }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex gap-3">
      <span className="text-xs font-semibold text-slate-600 mt-0.5 w-5 flex-shrink-0">{index + 1}</span>
      <div className="min-w-0">
        <p className="text-xs font-medium text-slate-200 leading-snug line-clamp-2">{citation.title}</p>
        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
          {citation.year > 0 && (
            <span className="text-xs text-slate-500">{citation.year}</span>
          )}
          {citation.domain && (
            <DomainBadge domain={citation.domain} />
          )}
          {citation.doi && (
            <span className="text-xs text-slate-600 font-mono truncate max-w-[200px]">{citation.doi}</span>
          )}
        </div>
      </div>
    </div>
  );
}

function PathCard({ path, index }: { path: GraphPath; index: number }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-semibold text-slate-500">PATH {index + 1}</span>
        <span className="text-xs text-slate-600">{path.hops} hop{path.hops !== 1 ? "s" : ""}</span>
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        {path.nodes.map((node, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <div className="flex flex-col items-start gap-1">
              <span className="text-xs font-medium text-white">{node.name}</span>
              <DomainBadge domain={node.domain} />
            </div>
            {i < path.relations.length && (
              <div className="flex items-center gap-1 mx-1">
                <div className="h-px w-4 bg-slate-600" />
                <span className="text-xs text-indigo-400 font-mono">{path.relations[i]}</span>
                <div className="h-px w-4 bg-slate-600" />
                <span className="text-slate-600 text-xs">›</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [user, setUser] = useState<{ full_name: string; email: string } | null>(null);
  const [queryText, setQueryText] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) { window.location.href = "/login"; return; }
    api.me(token)
      .then((u) => setUser({ full_name: u.full_name, email: u.email }))
      .catch(() => { clearTokens(); window.location.href = "/login"; });
  }, []);

  async function handleQuery(e: React.FormEvent) {
    e.preventDefault();
    if (!queryText.trim() || loading) return;
    const token = localStorage.getItem("access_token");
    if (!token) { window.location.href = "/login"; return; }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.query(token, { query: queryText });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    const token = localStorage.getItem("access_token");
    if (token) api.logout(token).catch(() => {});
    clearTokens();
    window.location.href = "/login";
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Nav */}
      <header className="relative border-b border-white/10 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center shadow shadow-indigo-500/30">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-white tracking-tight">Insight Engine</span>
          </div>
          <div className="flex items-center gap-4">
            {user && <span className="text-xs text-slate-400 hidden sm:block">{user.email}</span>}
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/5 text-xs font-medium transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="relative max-w-4xl mx-auto px-6 py-10">
        {/* Greeting */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white tracking-tight">
            {user ? `Hi, ${user.full_name.split(" ")[0]}` : "Dashboard"}
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Ask a cross-domain question — the knowledge graph has 1.5M entities across 12 domains.
          </p>
        </div>

        {/* Query box */}
        <form onSubmit={handleQuery} className="mb-8">
          <div className="bg-slate-900/80 border border-white/10 rounded-2xl p-4 flex flex-col gap-3">
            <input
              ref={inputRef}
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="e.g. aerospace materials for cardiac implants"
              className="w-full px-4 py-3 rounded-xl border border-white/10 bg-white/5 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
              disabled={loading}
            />
            <div className="flex items-center justify-between">
              <div className="flex gap-2 flex-wrap">
                {["aerospace materials for cardiac implants", "battery tech for pacemakers", "quantum sensors for brain imaging"].map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => { setQueryText(ex); inputRef.current?.focus(); }}
                    className="text-xs text-slate-500 hover:text-indigo-400 transition-colors"
                  >
                    &ldquo;{ex}&rdquo;
                  </button>
                ))}
              </div>
              <button
                type="submit"
                disabled={loading || !queryText.trim()}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:text-indigo-500 text-white text-sm font-semibold transition-colors shadow-lg shadow-indigo-500/20 whitespace-nowrap"
              >
                {loading ? "Searching…" : "Search"}
              </button>
            </div>
          </div>
        </form>

        {/* Loading state */}
        {loading && (
          <div className="bg-slate-900/80 border border-white/10 rounded-2xl p-8 text-center">
            <div className="inline-flex items-center gap-3 text-slate-400">
              <svg className="w-5 h-5 animate-spin text-indigo-400" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className="text-sm">Traversing knowledge graph + synthesising with Mistral…</span>
            </div>
            <p className="mt-2 text-xs text-slate-600">This takes ~30s — embedding → Qdrant → Neo4j → LLM</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-2xl bg-red-500/10 border border-red-500/30 px-6 py-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Meta */}
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span>{result.paths.length} cross-domain path{result.paths.length !== 1 ? "s" : ""} found</span>
              <span>·</span>
              <span>Confidence {Math.round(result.confidence * 100)}%</span>
              <span>·</span>
              <span>{(result.latency_ms / 1000).toFixed(1)}s</span>
            </div>

            {/* Answer */}
            <div className="bg-slate-900/80 border border-indigo-500/30 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-5 h-5 rounded-md bg-indigo-600 flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Mistral synthesis</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{result.answer}</p>
            </div>

            {/* Seed entities */}
            {result.seed_entities.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Seed entities</h3>
                <div className="flex flex-wrap gap-2">
                  {result.seed_entities.map((s) => (
                    <span key={s} className="text-xs px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-slate-400">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Paths */}
            {result.paths.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  Cross-domain paths
                </h3>
                <div className="space-y-3">
                  {result.paths.slice(0, 10).map((p, i) => (
                    <PathCard key={i} path={p} index={i} />
                  ))}
                  {result.paths.length > 10 && (
                    <p className="text-xs text-slate-600 text-center">
                      + {result.paths.length - 10} more paths
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Source citations */}
            {result.sources && result.sources.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  Source papers
                </h3>
                <div className="space-y-2">
                  {result.sources.slice(0, 15).map((s, i) => (
                    <CitationCard key={s.doc_id} citation={s} index={i} />
                  ))}
                  {result.sources.length > 15 && (
                    <p className="text-xs text-slate-600 text-center">
                      + {result.sources.length - 15} more papers
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!loading && !result && !error && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {MODULES.map((m) => (
              <div key={m.title} className="bg-slate-900/80 border border-white/10 rounded-2xl p-5 flex gap-4">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${m.color}`}>
                  <m.Icon />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white mb-1">{m.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{m.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function BoltIcon() {
  return <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>;
}
function TrendIcon() {
  return <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>;
}
function ShieldIcon() {
  return <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>;
}
function SearchIcon() {
  return <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>;
}

const MODULES = [
  { title: "Cross-Pollination Discovery", description: "Find technologies from Domain A that solve unsolved problems in Domain B.", color: "bg-indigo-600", Icon: BoltIcon },
  { title: "Trend Velocity Tracking", description: "Detect technologies being cited across multiple industries before mainstream.", color: "bg-violet-600", Icon: TrendIcon },
  { title: "Patent Portfolio De-Risking", description: "Surface prior art via graph topology, not keyword similarity.", color: "bg-blue-600", Icon: ShieldIcon },
  { title: "Automated Gap Analysis", description: "Use unconnected graph nodes to flag research white-spaces.", color: "bg-cyan-600", Icon: SearchIcon },
];

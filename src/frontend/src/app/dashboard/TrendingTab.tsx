"use client";

import React, { useEffect, useState } from "react";
import { api, TrendingEntity } from "@/lib/api";

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

interface Props {
  onAddToWatchlist: (entity: { entity_name: string; entity_type: string; entity_domain: string }) => void;
  onExplore: (entityName: string) => void;
}

export default function TrendingTab({ onAddToWatchlist, onExplore }: Props) {
  const [items, setItems] = useState<TrendingEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [added, setAdded] = useState<Set<string>>(new Set());

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    api.trending(token)
      .then(setItems)
      .catch(() => setError("Could not load trending data"))
      .finally(() => setLoading(false));
  }, []);

  // Find max for bar scaling
  const maxConnections = items[0]?.cross_domain_connections ?? 1;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-500 text-sm">
        <svg className="w-4 h-4 animate-spin mr-2 text-indigo-400" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Querying knowledge graph…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl bg-red-500/10 border border-red-500/30 px-6 py-4 text-sm text-red-400">
        {error}
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs text-slate-500 mb-4">
        Top entities ranked by cross-domain connections — the most interconnected technologies across all 12 domains.
      </p>
      <div className="space-y-2">
        {items.map((item, i) => {
          const domainCls = DOMAIN_COLORS[item.domain] ?? "bg-white/10 text-slate-300";
          const barWidth = Math.round((item.cross_domain_connections / maxConnections) * 100);
          const isAdded = added.has(item.name);
          return (
            <div key={item.name} className="bg-slate-900/80 border border-white/10 rounded-xl px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-slate-600 w-5 flex-shrink-0">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-sm font-medium text-white truncate">{item.name}</span>
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${domainCls}`}>
                      {item.domain}
                    </span>
                    <span className="text-xs text-slate-600 flex-shrink-0">{item.type}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-white/5 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-full bg-indigo-500/60 rounded-full transition-all"
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-500 flex-shrink-0 w-16 text-right">
                      {item.cross_domain_connections.toLocaleString()} links
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <button
                    onClick={() => onExplore(item.name)}
                    className="p-1.5 rounded-lg hover:bg-white/5 text-slate-500 hover:text-indigo-300 transition-colors"
                    title="Explore graph"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                  </button>
                  <button
                    onClick={() => {
                      onAddToWatchlist({ entity_name: item.name, entity_type: item.type, entity_domain: item.domain });
                      setAdded((prev) => { const s = new Set(prev); s.add(item.name); return s; });
                    }}
                    disabled={isAdded}
                    className={`p-1.5 rounded-lg transition-colors ${
                      isAdded
                        ? "text-emerald-400 bg-emerald-500/10"
                        : "hover:bg-white/5 text-slate-500 hover:text-emerald-300"
                    }`}
                    title={isAdded ? "On watchlist" : "Add to watchlist"}
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      {isAdded
                        ? <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        : <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                      }
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

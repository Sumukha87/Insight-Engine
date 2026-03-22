"use client";

import React, { useEffect, useState } from "react";
import { api, WatchlistItem } from "@/lib/api";

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
  onExplore: (entityName: string) => void;
}

export default function WatchlistTab({ onExplore }: Props) {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    api.getWatchlist(token)
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  async function handleRemove(entity_name: string) {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    await api.removeWatchlist(token, entity_name);
    setItems((prev) => prev.filter((i) => i.entity_name !== entity_name));
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-500 text-sm">
        Loading watchlist…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-400 text-sm">Your watchlist is empty.</p>
        <p className="text-slate-600 text-xs mt-1">
          Add entities from query results to track them here.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {items.map((item) => {
        const domainCls = DOMAIN_COLORS[item.entity_domain] ?? "bg-white/10 text-slate-300";
        return (
          <div
            key={item.id}
            className="bg-slate-900/80 border border-white/10 rounded-2xl p-5 flex flex-col gap-3"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white truncate">{item.entity_name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{item.entity_type}</p>
              </div>
              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${domainCls}`}>
                {item.entity_domain}
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Added {new Date(item.added_at).toLocaleDateString("en-GB", {
                day: "numeric", month: "short", year: "numeric",
              })}
            </p>
            <div className="flex gap-2 mt-auto">
              <button
                onClick={() => onExplore(item.entity_name)}
                className="flex-1 py-1.5 rounded-lg border border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/10 text-xs font-medium transition-colors"
              >
                Explore graph
              </button>
              <button
                onClick={() => handleRemove(item.entity_name)}
                className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-600 hover:text-red-400 transition-colors"
                aria-label="Remove from watchlist"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

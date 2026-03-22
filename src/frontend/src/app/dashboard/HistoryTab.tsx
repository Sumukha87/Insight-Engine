"use client";

import React, { useEffect, useState } from "react";
import { api, HistoryItem } from "@/lib/api";

interface Props {
  onReplay: (queryText: string) => void;
}

export default function HistoryTab({ onReplay }: Props) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    api.history(token)
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-500 text-sm">
        Loading history…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-400 text-sm">No queries yet.</p>
        <p className="text-slate-600 text-xs mt-1">Your search history will appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="bg-slate-900/80 border border-white/10 rounded-xl px-5 py-3.5 flex items-center justify-between gap-4"
        >
          <div className="min-w-0 flex-1">
            <p className="text-sm text-slate-300 truncate">{item.query_text}</p>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-slate-600">
                {new Date(item.created_at).toLocaleString("en-GB", {
                  day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
                })}
              </span>
              {item.latency_ms && (
                <span className="text-xs text-slate-600">
                  {(item.latency_ms / 1000).toFixed(1)}s
                </span>
              )}
            </div>
          </div>
          <button
            onClick={() => onReplay(item.query_text)}
            className="px-3 py-1.5 rounded-lg border border-white/10 text-slate-400 hover:text-indigo-300 hover:border-indigo-500/40 text-xs font-medium transition-colors flex-shrink-0"
          >
            Re-run
          </button>
        </div>
      ))}
    </div>
  );
}

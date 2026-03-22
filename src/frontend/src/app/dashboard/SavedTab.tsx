"use client";

import React, { useEffect, useState } from "react";
import { api, SavedQueryItem, QueryResponse } from "@/lib/api";

interface Props {
  onReplay: (queryText: string, result: QueryResponse) => void;
}

export default function SavedTab({ onReplay }: Props) {
  const [items, setItems] = useState<SavedQueryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    api.listSaved(token)
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id: string) {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    await api.deleteSaved(token, id);
    setItems((prev) => prev.filter((i) => i.id !== id));
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-500 text-sm">
        Loading saved queries…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-400 text-sm">No saved queries yet.</p>
        <p className="text-slate-600 text-xs mt-1">Run a query and click &ldquo;Save&rdquo; to store it here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} className="bg-slate-900/80 border border-white/10 rounded-2xl p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-semibold text-white truncate">{item.name}</h3>
              <p className="text-xs text-slate-500 mt-0.5 truncate">{item.query_text}</p>
              {item.notes && (
                <p className="text-xs text-slate-400 mt-1 italic">{item.notes}</p>
              )}
              <p className="text-xs text-slate-600 mt-2">
                {new Date(item.created_at).toLocaleDateString("en-GB", {
                  day: "numeric", month: "short", year: "numeric",
                })}
              </p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                className="px-3 py-1.5 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/5 text-xs font-medium transition-colors"
              >
                {expandedId === item.id ? "Hide" : "View"}
              </button>
              <button
                onClick={() => onReplay(item.query_text, item.result as QueryResponse)}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
              >
                Replay
              </button>
              <button
                onClick={() => handleDelete(item.id)}
                className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-600 hover:text-red-400 transition-colors"
                aria-label="Delete"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>

          {expandedId === item.id && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-2">Answer</p>
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                {(item.result as QueryResponse).answer}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

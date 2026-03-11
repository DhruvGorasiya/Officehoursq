"use client";

import React from "react";

interface SimilarQuestion {
  id: string;
  title: string;
  resolution_note?: string | null;
  helpful_votes?: number;
}

interface SimilarQuestionsPanelProps {
  questions: SimilarQuestion[];
  loading: boolean;
  error: string | null;
  onDismiss: () => void;
}

export default function SimilarQuestionsPanel({
  questions,
  loading,
  error,
  onDismiss,
}: SimilarQuestionsPanelProps) {
  if (!loading && !error && questions.length === 0) {
    return null;
  }

  return (
    <div className="mb-5">
      <div className="bg-cyan-500/10 border border-cyan-500/40 rounded-card p-4 shadow-sm">
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-cyan-300">
              Similar resolved questions
            </p>
            <p className="text-xs text-text-muted">
              These might already answer what you&apos;re asking.
            </p>
          </div>
          <button
            type="button"
            onClick={onDismiss}
            className="text-xs text-text-muted hover:text-text-primary underline-offset-2 hover:underline"
          >
            Dismiss
          </button>
        </div>

        {loading && (
          <p className="text-sm text-text-secondary">Searching past questions...</p>
        )}

        {error && (
          <p className="text-xs text-red mt-1">
            {error || "Unable to load similar questions."}
          </p>
        )}

        {!loading && !error && questions.length > 0 && (
          <div className="space-y-3 mt-2">
            {questions.map((q) => (
              <div
                key={q.id}
                className="bg-surface/60 border border-cyan-500/20 rounded-input px-3 py-2"
              >
                <p className="text-sm font-medium text-text-primary line-clamp-2">
                  {q.title}
                </p>
                {q.resolution_note && (
                  <p className="text-xs text-text-secondary mt-1 line-clamp-2">
                    {q.resolution_note.length > 140
                      ? q.resolution_note.slice(0, 140) + "…"
                      : q.resolution_note}
                  </p>
                )}
                {typeof q.helpful_votes === "number" && q.helpful_votes > 0 && (
                  <p className="text-[11px] text-cyan-300 mt-1">
                    {q.helpful_votes} found this helpful
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


"use client";

import React, { useState } from "react";
import { Sparkles } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { markQuestionHelpful } from "@/lib/knowledgeBaseApi";

interface HelpfulVoteButtonProps {
  questionId: string;
  initialCount: number;
}

export default function HelpfulVoteButton({
  questionId,
  initialCount,
}: HelpfulVoteButtonProps) {
  const { token } = useAuth();
  const [count, setCount] = useState(initialCount);
  const [hasVoted, setHasVoted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    if (!token || hasVoted || loading) return;

    setLoading(true);
    setError(null);

    try {
      const res = await markQuestionHelpful({ questionId, token });
      if (res.success) {
        const updated = res.data;
        if (updated && typeof updated.helpful_votes === "number") {
          setCount(updated.helpful_votes);
        } else {
          setCount((prev) => prev + 1);
        }
        setHasVoted(true);
      } else if (res.message === "Already voted helpful") {
        setHasVoted(true);
      } else {
        setError(res.message || "Could not record vote");
      }
    } catch (e) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={handleClick}
        disabled={loading || hasVoted}
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
          hasVoted
            ? "bg-green/10 border-green/40 text-green"
            : "bg-surface border-border text-text-secondary hover:text-text-primary hover:border-text-muted"
        } ${loading ? "opacity-70 cursor-not-allowed" : ""}`}
      >
        <Sparkles className="w-3 h-3" />
        <span>{hasVoted ? "Marked helpful" : "Mark helpful"}</span>
        <span className="text-[11px] text-text-muted">· {count}</span>
      </button>
      {error && <p className="text-[11px] text-red">{error}</p>}
    </div>
  );
}


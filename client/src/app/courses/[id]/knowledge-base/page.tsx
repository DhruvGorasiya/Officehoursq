"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import NavBar from "@/components/common/NavBar";
import { fetchKnowledgeBase } from "@/lib/knowledgeBaseApi";
import HelpfulVoteButton from "@/components/questions/HelpfulVoteButton";

interface KnowledgeBaseItem {
  id: string;
  title: string;
  description: string;
  category: string;
  resolution_note?: string | null;
  helpful_votes: number;
  resolved_at?: string | null;
  created_at: string;
  student_name?: string | null;
}

const PAGE_SIZE = 20;

export default function CourseKnowledgeBasePage() {
  const { user, token } = useAuth();
  const params = useParams();
  const courseId = params?.id as string;

  const [items, setItems] = useState<KnowledgeBaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [category, setCategory] = useState<string>("");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // debounce search input
  useEffect(() => {
    const handle = setTimeout(() => {
      setDebouncedSearch(search.trim());
      setPage(1);
    }, 400);
    return () => clearTimeout(handle);
  }, [search]);

  useEffect(() => {
    if (!token || !courseId) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchKnowledgeBase({
          courseId,
          search: debouncedSearch || undefined,
          category: category || undefined,
          page,
          token,
        });

        if (res.success) {
          setItems(res.data || []);
          setTotalCount(res.total_count ?? (res.data ? res.data.length : 0));
        } else {
          setError(res.message || "Failed to load knowledge base");
        }
      } catch (e) {
        setError("Network error loading knowledge base");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [token, courseId, debouncedSearch, category, page]);

  const totalPages =
    totalCount > 0 ? Math.ceil(totalCount / PAGE_SIZE) : page;

  return (
    <div className="min-h-screen bg-bg">
      <NavBar />

      <main className="max-w-3xl mx-auto p-6 md:p-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">
          Knowledge Base
        </h1>
        <p className="text-text-secondary mb-6">
          Browse resolved questions from this course&apos;s past sessions.
        </p>

        <div className="bg-card border border-border rounded-card p-4 mb-6 space-y-3">
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1">
              Search
            </label>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title, description, or resolution..."
              className="w-full bg-surface border border-border rounded-input px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  setPage(1);
                }}
                className="w-full bg-surface border border-border rounded-input px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="">All</option>
                <option value="debugging">Debugging</option>
                <option value="conceptual">Conceptual</option>
                <option value="setup">Environment Setup</option>
                <option value="assignment">Assignment Help</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="flex items-end justify-end text-xs text-text-muted">
              {totalCount > 0 && (
                <span>
                  Showing {(page - 1) * PAGE_SIZE + 1}-
                  {Math.min(page * PAGE_SIZE, totalCount)} of {totalCount}
                </span>
              )}
            </div>
          </div>
        </div>

        {loading && (
          <div className="text-center text-text-secondary py-8">
            Loading knowledge base...
          </div>
        )}

        {error && !loading && (
          <div className="text-red text-sm mb-4 bg-red/10 p-3 rounded-input border border-red/20">
            {error}
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="bg-surface border border-border rounded-card p-10 text-center text-text-secondary">
            No resolved questions found yet for this course.
          </div>
        )}

        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-card border border-border rounded-card p-4 shadow-sm"
            >
              <div className="flex justify-between items-start gap-4 mb-2">
                <div>
                  <h2 className="text-lg font-semibold text-text-primary mb-1">
                    {item.title}
                  </h2>
                  <div className="flex flex-wrap items-center gap-2 text-xs mb-1">
                    <span
                      className={`px-2 py-0.5 rounded-full border ${
                        item.category === "debugging"
                          ? "bg-purple/10 text-purple border-purple/20"
                          : item.category === "setup"
                          ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/30"
                          : item.category === "conceptual"
                          ? "bg-green/10 text-green border-green/20"
                          : item.category === "assignment"
                          ? "bg-amber/10 text-amber border-amber/20"
                          : "bg-red/10 text-red border-red/20"
                      }`}
                    >
                      {item.category}
                    </span>
                    {item.student_name && (
                      <span className="text-text-muted">
                        Asked by {item.student_name}
                      </span>
                    )}
                    {item.resolved_at && (
                      <span className="text-text-muted">
                        · Resolved{" "}
                        {new Date(item.resolved_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <HelpfulVoteButton
                  questionId={item.id}
                  initialCount={item.helpful_votes || 0}
                />
              </div>
              {item.resolution_note && (
                <p className="text-sm text-text-secondary mt-1 line-clamp-3">
                  {item.resolution_note.length > 260
                    ? item.resolution_note.slice(0, 260) + "…"
                    : item.resolution_note}
                </p>
              )}
            </div>
          ))}
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-6 text-sm text-text-secondary">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className={`px-3 py-1.5 rounded-input border border-border ${
                page <= 1
                  ? "opacity-40 cursor-not-allowed"
                  : "hover:bg-surface/80"
              }`}
            >
              Previous
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className={`px-3 py-1.5 rounded-input border border-border ${
                page >= totalPages
                  ? "opacity-40 cursor-not-allowed"
                  : "hover:bg-surface/80"
              }`}
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  );
}


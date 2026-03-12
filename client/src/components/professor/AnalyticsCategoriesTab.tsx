"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchCategories } from "@/lib/analyticsApi";

interface AnalyticsCategoriesTabProps {
  courseId: string;
}

interface CategoryRow {
  category: string;
  count: number;
  percentage: number;
}

interface CategoriesData {
  categories: CategoryRow[];
  total_resolved: number;
  insight?: string | null;
}

const CATEGORY_LABELS: Record<string, string> = {
  debugging: "Debugging",
  setup: "Environment Setup",
  conceptual: "Conceptual",
  assignment: "Assignment Help",
  other: "Other",
};

const CATEGORY_COLORS: Record<string, string> = {
  debugging: "bg-purple-500",
  setup: "bg-cyan-500",
  conceptual: "bg-green",
  assignment: "bg-amber",
  other: "bg-red",
};

export function AnalyticsCategoriesTab({ courseId }: AnalyticsCategoriesTabProps) {
  const { token } = useAuth();
  const [data, setData] = useState<CategoriesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchCategories({ courseId, token });
        if (!cancelled) {
          if (res.success) {
            setData(res.data as CategoriesData);
          } else {
            setError(res.message || "Failed to load category analytics");
          }
        }
      } catch {
        if (!cancelled) {
          setError("Network error loading category analytics");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [courseId, token]);

  if (!token) {
    return (
      <p className="text-sm text-text-secondary">
        You must be signed in to view analytics.
      </p>
    );
  }

  if (loading) {
    return (
      <p className="text-sm text-text-secondary">
        Loading category analytics...
      </p>
    );
  }

  if (error) {
    return (
      <div className="bg-red/10 border border-red/40 rounded-card p-4 text-sm text-red">
        {error}
      </div>
    );
  }

  if (!data || data.categories.length === 0) {
    return (
      <p className="text-sm text-text-secondary">
        Not enough resolved questions yet to show a category breakdown.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-card border border-border rounded-card p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Question Categories
        </h2>
        <div className="space-y-3">
          {data.categories.map((cat) => {
            const label = CATEGORY_LABELS[cat.category] || cat.category;
            const color = CATEGORY_COLORS[cat.category] || "bg-indigo-500";
            return (
              <div key={cat.category}>
                <div className="flex items-center justify-between mb-1 text-xs">
                  <span className="text-text-secondary">{label}</span>
                  <span className="text-text-muted">
                    {cat.count} · {cat.percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
                  <div
                    className={`${color} h-2 rounded-full transition-all`}
                    style={{ width: `${Math.max(cat.percentage, 4)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-card border border-border rounded-card p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-text-primary mb-2">
          Insight
        </h2>
        <p className="text-sm text-text-secondary">
          {data.insight ||
            "As more questions are resolved, this section will highlight which categories students struggle with most."}
        </p>
      </div>
    </div>
  );
}


"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchTaPerformance } from "@/lib/analyticsApi";
import { Star } from "lucide-react";

interface AnalyticsTaPerformanceTabProps {
  courseId: string;
}

interface TaRow {
  id: string;
  name: string;
  initials: string;
  resolved_count: number;
  avg_resolve_minutes: number | null;
  rating: number;
}

interface TaPerformanceData {
  tas: TaRow[];
}

export function AnalyticsTaPerformanceTab({
  courseId,
}: AnalyticsTaPerformanceTabProps) {
  const { token } = useAuth();
  const [data, setData] = useState<TaPerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchTaPerformance({ courseId, token });
        if (!cancelled) {
          if (res.success) {
            setData(res.data as TaPerformanceData);
          } else {
            setError(res.message || "Failed to load TA performance analytics");
          }
        }
      } catch {
        if (!cancelled) {
          setError("Network error loading TA performance analytics");
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
        Loading TA performance analytics...
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

  if (!data || data.tas.length === 0) {
    return (
      <p className="text-sm text-text-secondary">
        No resolved questions yet to calculate TA performance.
      </p>
    );
  }

  const formatMinutes = (value: number | null) => {
    if (value == null) return "--";
    return `${value.toFixed(1)} min`;
  };

  return (
    <div className="space-y-4">
      {data.tas.map((ta) => (
        <div
          key={ta.id}
          className="bg-card border border-border rounded-card p-4 shadow-sm flex items-center justify-between gap-4"
        >
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-accent text-white font-semibold text-sm">
              {ta.initials}
            </div>
            <div>
              <p className="text-sm font-semibold text-text-primary">
                {ta.name}
              </p>
              <p className="text-xs text-text-secondary mt-1">
                {ta.resolved_count} questions resolved
              </p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-xs uppercase tracking-wide text-text-muted mb-1">
                Avg Resolve Time
              </p>
              <p className="text-sm font-semibold text-text-primary">
                {formatMinutes(ta.avg_resolve_minutes)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-wide text-text-muted mb-1">
                Rating
              </p>
              <div className="flex items-center justify-end gap-1">
                {Array.from({ length: 5 }).map((_, idx) => (
                  <Star
                    key={idx}
                    className={`w-4 h-4 ${
                      idx < ta.rating
                        ? "text-amber fill-amber"
                        : "text-text-muted"
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}


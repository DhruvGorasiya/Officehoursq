"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchOverview } from "@/lib/analyticsApi";

interface AnalyticsOverviewTabProps {
  courseId: string;
}

interface OverviewData {
  total_questions: number;
  avg_wait_minutes: number | null;
  avg_resolve_minutes: number | null;
  recent_sessions: {
    id: string;
    title: string;
    date: string | null;
    total_questions: number;
  }[];
}

export function AnalyticsOverviewTab({ courseId }: AnalyticsOverviewTabProps) {
  const { token } = useAuth();
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchOverview({ courseId, token });
        if (!cancelled) {
          if (res.success) {
            setData(res.data as OverviewData);
          } else {
            setError(res.message || "Failed to load overview analytics");
          }
        }
      } catch {
        if (!cancelled) {
          setError("Network error loading overview analytics");
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
        Loading overview analytics...
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

  if (!data) {
    return (
      <p className="text-sm text-text-secondary">No analytics data yet.</p>
    );
  }

  const formatMinutes = (value: number | null) => {
    if (value == null) return "--";
    return `${value.toFixed(1)} min`;
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-card p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-text-muted mb-1">
            Total Questions
          </p>
          <p className="text-2xl font-semibold text-text-primary">
            {data.total_questions}
          </p>
        </div>
        <div className="bg-card border border-border rounded-card p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-text-muted mb-1">
            Avg Wait Time
          </p>
          <p className="text-2xl font-semibold text-text-primary">
            {formatMinutes(data.avg_wait_minutes)}
          </p>
        </div>
        <div className="bg-card border border-border rounded-card p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-text-muted mb-1">
            Avg Resolve Time
          </p>
          <p className="text-2xl font-semibold text-text-primary">
            {formatMinutes(data.avg_resolve_minutes)}
          </p>
        </div>
      </div>

      <div className="bg-card border border-border rounded-card p-4 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-text-primary">
            Recent Sessions
          </h2>
          <span className="text-xs text-text-muted">
            Showing up to 5 recent sessions
          </span>
        </div>
        {data.recent_sessions.length === 0 ? (
          <p className="text-sm text-text-secondary">
            No sessions yet for this course.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {data.recent_sessions.map((session) => (
              <li
                key={session.id}
                className="flex items-center justify-between py-2 text-sm"
              >
                <div>
                  <p className="text-text-primary font-medium">
                    {session.title || "Untitled session"}
                  </p>
                  {session.date && (
                    <p className="text-xs text-text-muted">
                      {new Date(session.date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-text-primary font-medium">
                    {session.total_questions}
                  </p>
                  <p className="text-xs text-text-muted">questions</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}


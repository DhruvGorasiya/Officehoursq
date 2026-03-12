"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchTrends } from "@/lib/analyticsApi";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface AnalyticsTrendsTabProps {
  courseId: string;
}

interface TrendWeek {
  week_start: string;
  count: number;
}

interface TrendsData {
  weeks: TrendWeek[];
  peak_week: TrendWeek | null;
  peak_session: {
    session_id: string;
    title: string;
    question_count: number;
  } | null;
}

export function AnalyticsTrendsTab({ courseId }: AnalyticsTrendsTabProps) {
  const { token } = useAuth();
  const [data, setData] = useState<TrendsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchTrends({ courseId, token });
        if (!cancelled) {
          if (res.success) {
            setData(res.data as TrendsData);
          } else {
            setError(res.message || "Failed to load trends analytics");
          }
        }
      } catch {
        if (!cancelled) {
          setError("Network error loading trends analytics");
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
        Loading trends analytics...
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

  if (!data || data.weeks.length === 0) {
    return (
      <p className="text-sm text-text-secondary">
        Not enough data yet to show weekly trends.
      </p>
    );
  }

  const chartData = data.weeks.map((w) => {
    const date = new Date(w.week_start);
    const label = date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
    return { ...w, label };
  });

  return (
    <div className="space-y-6">
      <div className="bg-card border border-border rounded-card p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Weekly Question Volume
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ left: -20 }}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148, 163, 184, 0.15)"
                vertical
                horizontal
              />
              <XAxis
                dataKey="label"
                tick={{ fill: "#94A3B8", fontSize: 12 }}
                axisLine={{ stroke: "#1E293B" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#94A3B8", fontSize: 12 }}
                axisLine={{ stroke: "#1E293B" }}
                tickLine={false}
                allowDecimals={false}
              />
              <Tooltip
                cursor={{ fill: "rgba(148, 163, 184, 0.12)" }}
                contentStyle={{
                  backgroundColor: "#020617",
                  borderColor: "#1E293B",
                  borderRadius: 10,
                }}
                labelClassName="text-text-secondary text-xs"
              />
              <Bar
                dataKey="count"
                fill="url(#indigoGradient)"
                radius={[6, 6, 0, 0]}
              />
              <defs>
                <linearGradient
                  id="indigoGradient"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop offset="0%" stopColor="#6366F1" stopOpacity={0.95} />
                  <stop offset="100%" stopColor="#6366F1" stopOpacity={0.4} />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card border border-border rounded-card p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-text-muted mb-1">
            Peak Week
          </p>
          {data.peak_week ? (
            <>
              <p className="text-sm font-semibold text-text-primary">
                {new Date(data.peak_week.week_start).toLocaleDateString(
                  undefined,
                  { month: "short", day: "numeric", year: "numeric" }
                )}
              </p>
              <p className="text-xs text-text-secondary mt-1">
                {data.peak_week.count} questions
              </p>
            </>
          ) : (
            <p className="text-sm text-text-secondary">
              No peak week yet — not enough questions.
            </p>
          )}
        </div>
        <div className="bg-card border border-border rounded-card p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-text-muted mb-1">
            Peak Session
          </p>
          {data.peak_session ? (
            <>
              <p className="text-sm font-semibold text-text-primary">
                {data.peak_session.title || "Untitled session"}
              </p>
              <p className="text-xs text-text-secondary mt-1">
                {data.peak_session.question_count} questions
              </p>
            </>
          ) : (
            <p className="text-sm text-text-secondary">
              No peak session yet — not enough data.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}


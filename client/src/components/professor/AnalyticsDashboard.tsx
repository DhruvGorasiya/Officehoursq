"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { exportAnalyticsCsv } from "@/lib/analyticsApi";
import { AnalyticsOverviewTab } from "./AnalyticsOverviewTab";
import { AnalyticsCategoriesTab } from "./AnalyticsCategoriesTab";
import { AnalyticsTrendsTab } from "./AnalyticsTrendsTab";
import { AnalyticsTaPerformanceTab } from "./AnalyticsTaPerformanceTab";

interface AnalyticsDashboardProps {
  courseId: string;
}

type TabKey = "overview" | "categories" | "trends" | "ta";

const tabs: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "categories", label: "Categories" },
  { key: "trends", label: "Trends" },
  { key: "ta", label: "TA Performance" },
];

export function AnalyticsDashboard({ courseId }: AnalyticsDashboardProps) {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = async () => {
    if (!token) return;
    setExporting(true);
    setExportError(null);
    try {
      await exportAnalyticsCsv({ courseId, token });
    } catch (err: any) {
      setExportError(err?.message || "Failed to export CSV");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 md:px-0 py-6 md:py-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">
            Analytics Dashboard
          </h1>
          <p className="text-text-secondary text-sm mt-1">
            Insights into questions, trends, and TA performance for this
            course.
          </p>
        </div>
        <div className="flex flex-col items-stretch md:items-end gap-2">
          <button
            type="button"
            onClick={handleExport}
            disabled={!token || exporting}
            className="inline-flex items-center justify-center px-4 py-2 rounded-input border border-border bg-surface text-sm font-medium text-text-secondary hover:text-text-primary hover:border-text-muted disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            {exporting ? "Exporting..." : "Export CSV"}
          </button>
          {exportError && (
            <p className="text-xs text-red max-w-xs text-right">
              {exportError}
            </p>
          )}
        </div>
      </div>

      <div className="border-b border-border mb-6">
        <nav className="-mb-px flex flex-wrap gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`px-2 pb-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-accent text-text-primary"
                  : "border-transparent text-text-secondary hover:text-text-primary hover:border-border"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div>
        {activeTab === "overview" && (
          <AnalyticsOverviewTab courseId={courseId} />
        )}
        {activeTab === "categories" && (
          <AnalyticsCategoriesTab courseId={courseId} />
        )}
        {activeTab === "trends" && <AnalyticsTrendsTab courseId={courseId} />}
        {activeTab === "ta" && (
          <AnalyticsTaPerformanceTab courseId={courseId} />
        )}
      </div>
    </div>
  );
}


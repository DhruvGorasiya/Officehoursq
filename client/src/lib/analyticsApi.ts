const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface AnalyticsBaseParams {
  courseId: string;
  token: string;
}

export async function fetchOverview({
  courseId,
  token,
}: AnalyticsBaseParams) {
  const params = new URLSearchParams();
  params.set("course_id", courseId);

  const res = await fetch(`${API_URL}/analytics/overview?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return res.json();
}

export async function fetchCategories({
  courseId,
  token,
}: AnalyticsBaseParams) {
  const params = new URLSearchParams();
  params.set("course_id", courseId);

  const res = await fetch(
    `${API_URL}/analytics/categories?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return res.json();
}

export async function fetchTrends({ courseId, token }: AnalyticsBaseParams) {
  const params = new URLSearchParams();
  params.set("course_id", courseId);

  const res = await fetch(`${API_URL}/analytics/trends?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return res.json();
}

export async function fetchTaPerformance({
  courseId,
  token,
}: AnalyticsBaseParams) {
  const params = new URLSearchParams();
  params.set("course_id", courseId);

  const res = await fetch(
    `${API_URL}/analytics/ta-performance?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return res.json();
}

export async function exportAnalyticsCsv({
  courseId,
  token,
}: AnalyticsBaseParams) {
  const params = new URLSearchParams();
  params.set("course_id", courseId);

  const res = await fetch(`${API_URL}/analytics/export?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    // Try to parse JSON error if available
    try {
      const data = await res.json();
      throw new Error(data?.message || "Failed to export analytics CSV");
    } catch {
      throw new Error("Failed to export analytics CSV");
    }
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `analytics_${courseId}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}


"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import NavBar from "@/components/common/NavBar";
import { useAuth } from "@/context/AuthContext";
import { AnalyticsDashboard } from "@/components/professor/AnalyticsDashboard";

export default function CourseAnalyticsPage() {
  const { user, loading } = useAuth();
  const params = useParams();
  const router = useRouter();
  const courseId = params?.id as string;

  useEffect(() => {
    if (!loading && (!user || user.role !== "professor")) {
      // Non-professors should not access analytics; send them back to course detail.
      if (courseId) {
        router.replace(`/courses/${courseId}`);
      } else {
        router.replace("/dashboard");
      }
    }
  }, [user, loading, courseId, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-bg">
        <NavBar />
        <div className="p-8 text-center text-text-secondary">
          Loading analytics...
        </div>
      </div>
    );
  }

  if (!user || user.role !== "professor") {
    return null;
  }

  return (
    <div className="min-h-screen bg-bg">
      <NavBar />
      <main className="py-6 md:py-8">
        <AnalyticsDashboard courseId={courseId} />
      </main>
    </div>
  );
}


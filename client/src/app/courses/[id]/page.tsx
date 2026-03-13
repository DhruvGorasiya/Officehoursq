"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import NavBar from "@/components/common/NavBar";
import { Plus, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

interface Session {
  id: string;
  course_id: string;
  title: string;
  date: string;
  start_time: string;
  end_time: string;
  status: "scheduled" | "active" | "ended";
}

interface Course {
  id: string;
  name: string;
  invite_code: string;
  professor_id: string;
}

export default function CourseDetail() {
  const { user, token } = useAuth();
  const params = useParams();
  const router = useRouter();
  const courseId = params?.id as string;

  const [course, setCourse] = useState<Course | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || !courseId) return;

    const fetchCourseAndSessions = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;

        // Fetch course details
        const cRes = await fetch(`${apiUrl}/courses/${courseId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const cData = await cRes.json();
        if (cData.success) {
          setCourse(cData.data);
        } else {
          router.push("/dashboard");
          return;
        }

        // Fetch sessions
        const sRes = await fetch(`${apiUrl}/sessions?course_id=${courseId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const sData = await sRes.json();
        if (sData.success) {
          setSessions(sData.data);
        }
      } catch (_err) {
        console.error("Failed to fetch data");
      } finally {
        setIsLoading(false);
      }
    };

    fetchCourseAndSessions();
  }, [token, courseId, router]);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const response = await fetch(`${apiUrl}/sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          course_id: courseId,
          title,
          date,
          start_time: startTime,
          end_time: endTime,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setSessions([...sessions, data.data]);
        setShowCreateModal(false);
        setTitle("");
        setDate("");
        setStartTime("");
        setEndTime("");
      } else {
        setError(data.message || "Failed to create session");
      }
    } catch (_err) {
      setError("Network connection failed.");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg">
        <NavBar />
        <div className="p-8 text-center text-text-secondary">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg">
      <NavBar />

      <main className="max-w-4xl mx-auto p-6 md:p-8">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8 pb-6 border-b border-border">
          <div>
            <h1 className="text-3xl font-bold text-text-primary mb-2">
              {course?.name}
            </h1>
            {user?.role === "professor" && (
              <p className="text-sm text-text-muted">
                Invite Code:{" "}
                <span className="font-mono bg-surface border border-border px-2 py-1 rounded text-accent tracking-wider ml-1">
                  {course?.invite_code}
                </span>
              </p>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href={`/courses/${courseId}/knowledge-base`}
              className="px-4 py-2 rounded-input border border-border text-sm font-medium text-text-secondary hover:text-text-primary hover:border-text-muted transition-colors"
            >
              Knowledge Base
            </Link>
            {user?.role === "professor" && (
              <Link
                href={`/courses/${courseId}/analytics`}
                className="px-4 py-2 rounded-input border border-border text-sm font-medium text-text-secondary hover:text-text-primary hover:border-text-muted transition-colors"
              >
                Analytics
              </Link>
            )}
            {user?.role === "professor" && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-input font-medium transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create Session
              </button>
            )}
          </div>
        </div>

        <h2 className="text-xl font-bold text-text-primary mb-4">Sessions</h2>

        {sessions.length === 0 ? (
          <div className="bg-surface border border-border rounded-card p-12 text-center shadow-sm">
            <h3 className="text-lg font-medium text-text-primary mb-2">
              No sessions scheduled
            </h3>
            <p className="text-text-secondary">
              {user?.role === "professor"
                ? "Create a new session to get started."
                : "Wait for your professor to schedule a session."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {sessions.map((session) => (
              <Link href={`/sessions/${session.id}`} key={session.id}>
                <div className="bg-card hover:bg-surface border border-border rounded-card p-6 shadow-sm cursor-pointer transition-colors group">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="font-semibold text-text-primary text-lg group-hover:text-accent transition-colors">
                      {session.title}
                    </h3>
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${session.status === "active"
                          ? "bg-green/10 text-green"
                          : session.status === "scheduled"
                            ? "bg-blue-500/10 text-blue-400"
                            : "bg-surface text-text-muted"
                        }`}
                    >
                      {session.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-sm text-text-secondary space-y-1">
                    <p>Date: {session.date}</p>
                    <p>
                      Time: {session.start_time} - {session.end_time}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>

      {/* Create Session Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex flex-col items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-card rounded-card border border-border p-6 w-full max-w-md shadow-xl my-8">
            <h2 className="text-xl font-bold text-text-primary mb-4">
              Create New Session
            </h2>
            {error && (
              <div className="text-red text-sm mb-4 bg-red/10 p-3 rounded-input">
                {error}
              </div>
            )}
            <form onSubmit={handleCreateSession}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Session Title
                </label>
                <input
                  id="sessionTitle"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-surface border border-border rounded-input px-4 py-2 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  placeholder="e.g. Midterm Review"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Date
                </label>
                <input
                  id="sessionDate"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full bg-surface border border-border rounded-input px-4 py-2 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Start Time
                  </label>
                  <input
                    id="startTime"
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full bg-surface border border-border rounded-input px-4 py-2 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    End Time
                  </label>
                  <input
                    id="endTime"
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full bg-surface border border-border rounded-input px-4 py-2 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6 border-t border-border pt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 font-medium text-text-secondary hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-accent text-white px-4 py-2 rounded-input font-medium hover:bg-accent/90 transition-colors"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

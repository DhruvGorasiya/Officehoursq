"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import NavBar from "@/components/common/NavBar";
import QuestionSubmissionForm from "@/components/questions/QuestionSubmissionForm";
import { ArrowLeft, Play, Square, MessageSquare, CheckCircle, Clock, AlertCircle, ChevronDown } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useRealtimeChannel } from "@/hooks/useRealtimeChannel";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { dot: string; bg: string; text: string; label: string }> = {
    active: { dot: 'bg-green', bg: 'bg-green/10', text: 'text-green', label: 'Active' },
    scheduled: { dot: 'bg-amber', bg: 'bg-amber/10', text: 'text-amber', label: 'Scheduled' },
    ended: { dot: 'bg-text-muted', bg: 'bg-surface', text: 'text-text-muted', label: 'Ended' },
  };
  const c = config[status] || config.ended;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-badge text-xs font-semibold ${c.bg} ${c.text} border border-current/20`}>
      <span className={`w-2 h-2 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}

export default function SessionView() {
  const { user, token } = useAuth();
  const params = useParams();
  const router = useRouter();
  const sessionId = params?.id as string;

  const [sessionInfo, setSessionInfo] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null);

  const fetchSessionAndQuestions = async () => {
    if (!token || !sessionId) return;
    try {
      const [sessionRes, qRes] = await Promise.all([
        fetch(`${API_URL}/sessions/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_URL}/questions?session_id=${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      const sessionData = await sessionRes.json();
      if (sessionData.success) {
        setSessionInfo(sessionData.data);
      }

      const qData = await qRes.json();
      if (qData.success) {
        setQuestions(qData.data);
      }
    } catch (err) {
      console.error('Failed to fetch data', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionAndQuestions();
    const interval = setInterval(fetchSessionAndQuestions, 10000);
    return () => clearInterval(interval);
  }, [token, sessionId]);

  // Realtime: refresh questions and session when events arrive for this session
  useRealtimeChannel(
    sessionId ? `session:${sessionId}` : null,
    {
      onQuestionEvent: () => {
        // For v1, simply refetch to keep client logic simple and consistent.
        fetchSessionAndQuestions();
      },
      onSessionEvent: () => {
        fetchSessionAndQuestions();
      },
      onQueueUpdatedEvent: () => {
        fetchSessionAndQuestions();
      },
    }
  );

  const handleStatusChange = async (newStatus: string) => {
    try {
      const res = await fetch(`${API_URL}/sessions/${sessionId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setSessionInfo((prev: any) => (prev ? { ...prev, status: newStatus } : prev));
        fetchSessionAndQuestions();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAction = async (action: 'claim' | 'resolve' | 'defer' | 'withdraw', questionId: string) => {
    try {
      const body = action === 'resolve' ? { resolution_note: 'Resolved by TA' } : {};
      const res = await fetch(`${API_URL}/questions/${questionId}/${action}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined,
      });
      if (res.ok) {
        fetchSessionAndQuestions();
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg">
        <NavBar />
        <div className="p-8 text-center text-text-secondary">Loading session...</div>
      </div>
    );
  }

  const isStaff = user?.role === "professor" || user?.role === "ta";
  const sessionStatus = sessionInfo?.status || "scheduled";

  // Student view: include deferred in active question check
  const activeQuestion = questions.find((q) =>
    ["queued", "in_progress", "deferred"].includes(q.status)
  );

  // TA view: split into sections
  const allActive = questions
    .filter((q) => ["queued", "in_progress", "deferred"].includes(q.status))
    .sort((a, b) => a.queue_position - b.queue_position);
  const inProgressQueue = allActive.filter((q) => q.status === "in_progress");
  const waitingQueue = allActive.filter((q) => q.status === "queued" || q.status === "deferred");

  const queuedCount = questions.filter((q) => q.status === "queued" || q.status === "deferred").length;
  const inProgressCount = questions.filter((q) => q.status === "in_progress").length;
  const resolvedCount = questions.filter((q) => q.status === "resolved").length;

  return (
    <div className="min-h-screen bg-bg">
      <NavBar
        title={sessionInfo?.course_name || 'OfficeHoursQ'}
        statusBadge={sessionStatus === 'active' ? 'active' : sessionStatus === 'scheduled' ? 'scheduled' : null}
      />

      <main className="max-w-5xl mx-auto p-6 md:p-8">
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        </div>

        {/* Session Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b border-border pb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-text-primary">
                {sessionInfo?.title || 'Office Hours Session'}
              </h1>
              <StatusBadge status={sessionStatus} />
            </div>
            <p className="text-text-secondary">
              {sessionInfo?.course_name && <span className="font-medium">{sessionInfo.course_name}</span>}
              {sessionInfo?.date && (
                <span className="ml-2 text-text-muted">
                  {sessionInfo.date}
                  {sessionInfo.start_time && sessionInfo.end_time && (
                    <> &middot; {sessionInfo.start_time} – {sessionInfo.end_time}</>
                  )}
                </span>
              )}
            </p>
            {sessionInfo?.course_id && (
              <div className="mt-2">
                <Link
                  href={`/courses/${sessionInfo.course_id}/knowledge-base`}
                  className="text-xs text-text-muted underline-offset-2 hover:underline hover:text-text-primary"
                >
                  View course knowledge base
                </Link>
              </div>
            )}
          </div>

          {user?.role === 'professor' && (
            <div className="flex gap-3">
              {sessionStatus === 'scheduled' && (
                <button
                  onClick={() => handleStatusChange('active')}
                  className="flex items-center gap-2 bg-green/10 text-green border border-green/20 hover:bg-green/20 px-4 py-2 rounded-input font-medium transition-colors"
                >
                  <Play className="w-4 h-4" /> Start
                </button>
              )}
              {sessionStatus === 'active' && (
                <button
                  onClick={() => handleStatusChange('ended')}
                  className="flex items-center gap-2 bg-red/10 text-red border border-red/20 hover:bg-red/20 px-4 py-2 rounded-input font-medium transition-colors"
                >
                  <Square className="w-4 h-4" /> End
                </button>
              )}
            </div>
          )}
        </div>

        {!isStaff ? (
          /* ───── Student View ───── */
          <div className="py-4">
            <QuestionSubmissionForm
              sessionId={sessionId}
              onSuccess={fetchSessionAndQuestions}
              activeQuestion={activeQuestion}
              onWithdraw={(id) => handleAction('withdraw', id)}
              courseId={sessionInfo?.course_id}
            />
          </div>
        ) : (
          /* ───── TA / Professor View ───── */
          <div className="max-w-[600px] mx-auto">
            {/* Stats Row */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-card border border-border rounded-card p-4 text-center">
                <p className="text-xs text-text-muted uppercase tracking-wider mb-1">Queued</p>
                <p className="text-2xl font-bold text-accent">{queuedCount}</p>
              </div>
              <div className="bg-card border border-border rounded-card p-4 text-center">
                <p className="text-xs text-text-muted uppercase tracking-wider mb-1">In Progress</p>
                <p className="text-2xl font-bold text-amber">{inProgressCount}</p>
              </div>
              <div className="bg-card border border-border rounded-card p-4 text-center">
                <p className="text-xs text-text-muted uppercase tracking-wider mb-1">Resolved</p>
                <p className="text-2xl font-bold text-green">{resolvedCount}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 mb-6">
              <h2 className="text-xl font-bold text-text-primary">Live Queue</h2>
              <span className="bg-accent/20 text-accent px-3 py-1 rounded-full text-sm font-bold">
                {allActive.length} Active
              </span>
            </div>

            {allActive.length === 0 ? (
              <div className="bg-surface border border-border rounded-card p-12 text-center shadow-sm">
                <MessageSquare className="w-12 h-12 text-text-muted mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium text-text-primary mb-2">No questions in queue. Nice work!</h3>
                <p className="text-text-secondary">Students haven&apos;t submitted any questions yet.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* In Progress Section */}
                {inProgressQueue.length > 0 && (
                  <>
                    {inProgressQueue.map((q) => {
                      const isExpanded = expandedQuestionId === q.id;
                      return (
                        <div
                          key={q.id}
                          data-testid="question-card"
                          className="bg-card border-2 border-amber rounded-card p-5 shadow-sm shadow-amber/5"
                        >
                          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
                            <div className="bg-surface text-text-primary px-4 py-3 rounded-input text-center min-w-[80px] border border-border/50 shrink-0">
                              <div className="text-xs text-text-secondary mb-1">POS</div>
                              <div className="text-2xl font-bold">{q.queue_position}</div>
                            </div>

                            <div className="grow">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold text-text-primary text-lg">{q.title}</h3>
                                <span className="bg-amber/10 text-amber text-xs px-2 py-0.5 rounded border border-amber/20 flex items-center gap-1">
                                  <CheckCircle className="w-3 h-3" /> In Progress
                                </span>
                              </div>
                              <p className="text-text-secondary text-sm mb-2">
                                {q.student?.name} &bull; <span className="text-text-muted">{q.category}</span>
                                {q.claimer?.name && (
                                  <span className="ml-2 text-amber">Claimed by {q.claimer.name}</span>
                                )}
                              </p>
                              <p className="text-sm text-text-primary line-clamp-2 bg-[#0D1117] p-2 rounded-md border border-border/50">
                                {q.description}
                              </p>
                            </div>

                            <div className="flex flex-col gap-2 shrink-0 w-full md:w-36">
                              <button
                                onClick={() => handleAction('resolve', q.id)}
                                className="w-full bg-green text-white hover:bg-green/90 px-3 py-2 rounded-input text-sm font-medium transition-colors"
                              >
                                Resolve
                              </button>
                              <button
                                onClick={() => handleAction('defer', q.id)}
                                className="w-full bg-surface border border-border hover:bg-surface/80 text-text-secondary px-3 py-2 rounded-input text-sm font-medium transition-colors"
                              >
                                Defer
                              </button>
                              <button
                                type="button"
                                onClick={() => setExpandedQuestionId(isExpanded ? null : q.id)}
                                className="w-full bg-surface border border-border/70 hover:bg-surface/80 text-text-muted hover:text-text-primary px-3 py-2 rounded-input text-xs font-medium transition-colors inline-flex items-center justify-center gap-1"
                              >
                                <span>{isExpanded ? 'Hide details' : 'View details'}</span>
                                <ChevronDown
                                  className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                />
                              </button>
                            </div>
                          </div>

                          {isExpanded && (
                            <div className="mt-4 pt-4 border-t border-border space-y-3">
                              <div>
                                <h4 className="text-xs font-semibold text-text-secondary mb-1">Description</h4>
                                <p className="text-sm text-text-primary whitespace-pre-wrap">{q.description}</p>
                              </div>
                              {q.code_snippet && (
                                <div>
                                  <h4 className="text-xs font-semibold text-text-secondary mb-1">Code Snippet</h4>
                                  <pre className="bg-[#0D1117] border border-border rounded-input px-3 py-2 text-xs text-text-primary font-mono whitespace-pre-wrap overflow-x-auto">
                                    {q.code_snippet}
                                  </pre>
                                </div>
                              )}
                              {q.error_message && (
                                <div>
                                  <h4 className="text-xs font-semibold text-text-secondary mb-1">Error Message</h4>
                                  <pre className="bg-red/10 border border-red/30 rounded-input px-3 py-2 text-xs text-red font-mono whitespace-pre-wrap overflow-x-auto">
                                    {q.error_message}
                                  </pre>
                                </div>
                              )}
                              {q.what_tried && (
                                <div>
                                  <h4 className="text-xs font-semibold text-text-secondary mb-1 italic">Tried</h4>
                                  <p className="text-sm text-text-primary whitespace-pre-wrap">{q.what_tried}</p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </>
                )}

                {/* Queued / Deferred Section */}
                {waitingQueue.map((q) => {
                  const isExpanded = expandedQuestionId === q.id;
                  return (
                    <div
                      key={q.id}
                      data-testid="question-card"
                      className="bg-card border border-border rounded-card p-5 shadow-sm transition-all hover:border-text-muted hover:shadow-md"
                    >
                      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
                        <div className="bg-surface text-text-primary px-4 py-3 rounded-input text-center min-w-[80px] border border-border/50 shrink-0">
                          <div className="text-xs text-text-secondary mb-1">POS</div>
                          <div className="text-2xl font-bold">{q.queue_position}</div>
                        </div>

                        <div className="grow">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-text-primary text-lg">{q.title}</h3>
                            <span className="text-xs px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                              {q.category}
                            </span>
                            <span
                              className={`text-xs px-2 py-0.5 rounded border ${
                                q.priority === 'high'
                                  ? 'bg-red/10 text-red border-red/20'
                                  : q.priority === 'medium'
                                    ? 'bg-amber/10 text-amber border-amber/20'
                                    : 'bg-accent/10 text-accent border-accent/20'
                              }`}
                            >
                              {q.priority}
                            </span>
                            {q.status === 'deferred' && (
                              <span className="text-xs px-2 py-0.5 rounded bg-purple/10 text-purple border border-purple/20 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" /> Deferred
                              </span>
                            )}
                          </div>
                          <p className="text-text-secondary text-sm mb-2">
                            {q.student?.name} &bull;{" "}
                            <span className="text-text-muted">
                              {(() => {
                                const waitMinutes =
                                  q.estimated_wait_minutes ??
                                  (q.queue_position
                                    ? q.queue_position * 5
                                    : 5);
                                const label =
                                  waitMinutes >= 60
                                    ? "60+ min"
                                    : `${waitMinutes} min`;
                                return `~${label} wait`;
                              })()}
                            </span>
                          </p>
                          <p className="text-sm text-text-primary line-clamp-2 bg-[#0D1117] p-2 rounded-md border border-border/50">
                            {q.description}
                          </p>
                        </div>

                        <div className="flex flex-col gap-2 shrink-0 w-full md:w-36">
                          <button
                            onClick={() => handleAction('claim', q.id)}
                            className="w-full bg-accent hover:bg-accent/90 text-white px-3 py-2 rounded-input text-sm font-medium transition-colors"
                          >
                            Claim
                          </button>
                          <button
                            onClick={() => handleAction('resolve', q.id)}
                            className="w-full bg-green text-white hover:bg-green/90 px-3 py-2 rounded-input text-sm font-medium transition-colors"
                          >
                            Resolve
                          </button>
                          <button
                            onClick={() => handleAction('defer', q.id)}
                            className="w-full bg-surface border border-border hover:bg-surface/80 text-text-secondary px-3 py-2 rounded-input text-sm font-medium transition-colors"
                          >
                            Defer
                          </button>
                          <button
                            type="button"
                            onClick={() => setExpandedQuestionId(isExpanded ? null : q.id)}
                            className="w-full bg-surface border border-border/70 hover:bg-surface/80 text-text-muted hover:text-text-primary px-3 py-2 rounded-input text-xs font-medium transition-colors inline-flex items-center justify-center gap-1"
                          >
                            <span>{isExpanded ? 'Hide details' : 'View details'}</span>
                            <ChevronDown
                              className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                            />
                          </button>
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="mt-4 pt-4 border-t border-border space-y-3">
                          <div>
                            <h4 className="text-xs font-semibold text-text-secondary mb-1">Description</h4>
                            <p className="text-sm text-text-primary whitespace-pre-wrap">{q.description}</p>
                          </div>
                          {q.code_snippet && (
                            <div>
                              <h4 className="text-xs font-semibold text-text-secondary mb-1">Code Snippet</h4>
                              <pre className="bg-[#0D1117] border border-border rounded-input px-3 py-2 text-xs text-text-primary font-mono whitespace-pre-wrap overflow-x-auto">
                                {q.code_snippet}
                              </pre>
                            </div>
                          )}
                          {q.error_message && (
                            <div>
                              <h4 className="text-xs font-semibold text-text-secondary mb-1">Error Message</h4>
                              <pre className="bg-red/10 border border-red/30 rounded-input px-3 py-2 text-xs text-red font-mono whitespace-pre-wrap overflow-x-auto">
                                {q.error_message}
                              </pre>
                            </div>
                          )}
                          {q.what_tried && (
                            <div>
                              <h4 className="text-xs font-semibold text-text-secondary mb-1 italic">Tried</h4>
                              <p className="text-sm text-text-primary whitespace-pre-wrap">{q.what_tried}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

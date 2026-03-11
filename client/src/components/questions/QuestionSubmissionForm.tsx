"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { CheckCircle, Edit, Trash2, X } from "lucide-react";
import SimilarQuestionsPanel from "./SimilarQuestionsPanel";
import { fetchSimilarQuestions } from "@/lib/knowledgeBaseApi";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface QuestionSubmissionFormProps {
  sessionId: string;
  onSuccess: () => void;
  activeQuestion: any | null;
  onWithdraw: (id: string) => void;
  courseId?: string;
}

export default function QuestionSubmissionForm({
  sessionId,
  onSuccess,
  activeQuestion,
  onWithdraw,
  courseId,
}: QuestionSubmissionFormProps) {
  const { token } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [codeSnippet, setCodeSnippet] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [whatTried, setWhatTried] = useState("");
  const [category, setCategory] = useState("debugging");
  const [priority, setPriority] = useState("low");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  const [showSimilarPanel, setShowSimilarPanel] = useState(true);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [similarError, setSimilarError] = useState<string | null>(null);
  const [similarQuestions, setSimilarQuestions] = useState<any[]>([]);
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isEditing && activeQuestion) {
      setTitle(activeQuestion.title || "");
      setDescription(activeQuestion.description || "");
      setCodeSnippet(activeQuestion.code_snippet || "");
      setErrorMessage(activeQuestion.error_message || "");
      setWhatTried(activeQuestion.what_tried || "");
      setCategory(activeQuestion.category || "debugging");
      setPriority(activeQuestion.priority || "low");
    }
  }, [isEditing, activeQuestion]);

  const maybeFetchSimilar = useCallback(
    (currentTitle: string) => {
      if (!token || !courseId || !showSimilarPanel || currentTitle.length <= 5) {
        setSimilarQuestions([]);
        setSimilarError(null);
        setSimilarLoading(false);
        return;
      }

      setSimilarLoading(true);
      setSimilarError(null);

      fetchSimilarQuestions({
        courseId,
        title: currentTitle,
        token,
      })
        .then((res) => {
          if (res.success && Array.isArray(res.data)) {
            setSimilarQuestions(res.data);
          } else {
            setSimilarQuestions([]);
          }
        })
        .catch(() => {
          setSimilarError("Could not load similar questions.");
        })
        .finally(() => {
          setSimilarLoading(false);
        });
    },
    [token, courseId, showSimilarPanel]
  );

  useEffect(() => {
    if (!showSimilarPanel) return;

    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    const timer = setTimeout(() => {
      if (title && title.length > 5) {
        maybeFetchSimilar(title);
      } else {
        setSimilarQuestions([]);
        setSimilarError(null);
      }
    }, 400);

    setDebounceTimer(timer);

    return () => {
      clearTimeout(timer);
    };
  }, [title, maybeFetchSimilar, showSimilarPanel]);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setCodeSnippet("");
    setErrorMessage("");
    setWhatTried("");
    setCategory("debugging");
    setPriority("low");
    setError("");
    setShowSimilarPanel(true);
    setSimilarQuestions([]);
    setSimilarError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsSubmitting(true);
    setError("");

    try {
      const payload = {
        ...(isEditing ? {} : { session_id: sessionId }),
        title,
        description,
        code_snippet: codeSnippet || null,
        error_message: errorMessage || null,
        what_tried: whatTried,
        category,
        priority,
      };

      const url = isEditing
        ? `${API_URL}/questions/${activeQuestion.id}`
        : `${API_URL}/questions`;

      const response = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (data.success) {
        if (isEditing) setIsEditing(false);
        resetForm();
        onSuccess();
      } else {
        setError(data.message || "Failed to submit question");
      }
    } catch (err) {
      setError("Network error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (activeQuestion && !isEditing) {
    const isClaimed = activeQuestion.status === "in_progress";
    const isDeferred = activeQuestion.status === "deferred";

    return (
      <div className="bg-card w-full max-w-[520px] mx-auto rounded-card p-6 border border-border shadow-lg">
        <h2 className="text-xl font-bold text-text-primary mb-4">
          Queue Status
        </h2>

        {isClaimed ? (
          <div className="bg-green/10 border border-green text-green rounded-input p-4 flex items-center gap-3 mb-6">
            <CheckCircle className="w-6 h-6 shrink-0" />
            <div>
              <p className="font-semibold">Your question is being answered!</p>
              <p className="text-sm opacity-90">
                TA is reviewing your question now.
              </p>
            </div>
          </div>
        ) : isDeferred ? (
          <div className="bg-purple/10 border border-purple text-purple rounded-input p-4 flex items-center gap-3 mb-6">
            <CheckCircle className="w-6 h-6 shrink-0" />
            <div>
              <p className="font-semibold">Your question has been deferred</p>
              <p className="text-sm opacity-90">
                It has been moved to the back of the queue and will be addressed
                later.
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-surface border border-border rounded-input p-5 mb-6 text-center">
            <p className="text-text-secondary text-sm mb-1">Your Position</p>
            <p className="text-4xl font-bold text-accent">
              {activeQuestion.queue_position}
            </p>
            <p className="text-xs text-text-muted mt-2">
              Estimated wait: ~{Math.min(activeQuestion.queue_position * 5, 60)}
              {activeQuestion.queue_position * 5 > 60 ? "+" : ""} mins
            </p>
          </div>
        )}

        <div className="border-t border-border pt-4 mb-6">
          <h3 className="font-semibold text-text-primary text-lg mb-1">
            {activeQuestion.title}
          </h3>
          <p className="text-sm text-text-secondary line-clamp-2">
            {activeQuestion.description}
          </p>
          <div className="flex gap-2 mt-3">
            <span className="text-xs px-2 py-1 rounded-full bg-surface text-text-muted border border-border">
              {activeQuestion.category}
            </span>
            <span
              className={`text-xs px-2 py-1 rounded-full border ${
                activeQuestion.priority === "high"
                  ? "bg-red/10 text-red border-red/20"
                  : activeQuestion.priority === "medium"
                  ? "bg-amber/10 text-amber border-amber/20"
                  : "bg-blue-500/10 text-blue-400 border-blue-500/20"
              }`}
            >
              {activeQuestion.priority} priority
            </span>
          </div>
        </div>

        {/* Hide Edit/Withdraw when claimed (in_progress) */}
        {!isClaimed && (
          <div className="flex justify-end gap-3">
            {activeQuestion.status === "queued" && (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2 px-4 py-2 font-medium text-text-secondary hover:text-text-primary transition-colors bg-surface hover:bg-surface/80 rounded-input"
              >
                <Edit className="w-4 h-4" /> Edit
              </button>
            )}
            <button
              type="button"
              onClick={() => onWithdraw(activeQuestion.id)}
              className="flex items-center gap-2 px-4 py-2 font-medium text-red hover:bg-red/10 transition-colors border border-red/20 rounded-input"
            >
              <Trash2 className="w-4 h-4" /> Withdraw
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-card w-full max-w-[520px] mx-auto rounded-card p-6 border border-border shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-text-primary">
          {isEditing ? "Edit Question" : "Ask a Question"}
        </h2>
        {isEditing && (
          <button
            type="button"
            onClick={() => {
              setIsEditing(false);
              resetForm();
            }}
            className="text-text-muted hover:text-text-primary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {error && (
        <div className="text-red text-sm mb-4 bg-red/10 p-3 rounded-input border border-red/20">
          {error}
        </div>
      )}

      {showSimilarPanel && courseId && (
        <SimilarQuestionsPanel
          questions={similarQuestions}
          loading={similarLoading}
          error={similarError}
          onDismiss={() => setShowSimilarPanel(false)}
        />
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Title <span className="text-red">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={200}
            className="w-full bg-surface border border-border rounded-input px-4 py-2.5 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            placeholder="Brief summary of your issue"
            required
          />
          <div className="text-right text-xs text-text-muted mt-1">
            {title.length}/200
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Description <span className="text-red">*</span>
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={2000}
            rows={3}
            className="w-full bg-surface border border-border rounded-input px-4 py-3 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent resize-none"
            placeholder="Detailed description of what you're trying to do and what's going wrong"
            required
          />
          <div className="text-right text-xs text-text-muted mt-1">
            {description.length}/2000
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            What I&apos;ve Tried <span className="text-red">*</span>
          </label>
          <textarea
            value={whatTried}
            onChange={(e) => setWhatTried(e.target.value)}
            maxLength={2000}
            rows={2}
            className="w-full bg-surface border border-border rounded-input px-4 py-3 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent resize-none"
            placeholder="Steps you've already taken to solve this"
            required
          />
          <div className="text-right text-xs text-text-muted mt-1">
            {whatTried.length}/2000
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Code Snippet (Optional)
          </label>
          <textarea
            value={codeSnippet}
            onChange={(e) => setCodeSnippet(e.target.value)}
            maxLength={5000}
            rows={3}
            className="w-full bg-[#0D1117] border border-border rounded-input px-4 py-3 text-text-primary font-mono text-sm focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent resize-y"
            placeholder="Paste relevant code here..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Error Message (Optional)
          </label>
          <input
            type="text"
            value={errorMessage}
            onChange={(e) => setErrorMessage(e.target.value)}
            maxLength={1000}
            className="w-full bg-[#0D1117] border border-border rounded-input px-4 py-2.5 text-text-primary font-mono text-sm focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            placeholder="Paste exact error output"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-surface border border-border rounded-input px-4 py-2.5 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent appearance-none"
            >
              <option value="debugging">Debugging</option>
              <option value="conceptual">Conceptual</option>
              <option value="setup">Environment Setup</option>
              <option value="assignment">Assignment Help</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full bg-surface border border-border rounded-input px-4 py-2.5 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent appearance-none"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>

        <div className="pt-4">
          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full bg-accent text-white px-4 py-3 rounded-input font-bold text-lg transition-all ${
              isSubmitting
                ? "opacity-70 cursor-not-allowed"
                : "hover:bg-accent/90 hover:shadow-lg hover:shadow-accent/20"
            }`}
          >
            {isSubmitting
              ? isEditing
                ? "Saving..."
                : "Submitting..."
              : isEditing
              ? "Save Changes"
              : "Submit Question"}
          </button>
        </div>
      </form>
    </div>
  );
}

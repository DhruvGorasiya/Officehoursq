'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import NavBar from '@/components/common/NavBar';
import QuestionSubmissionForm from '@/components/questions/QuestionSubmissionForm';
import { ArrowLeft, Play, Square, MessageSquare, CheckCircle, Clock } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';

export default function SessionView() {
  const { user, token } = useAuth();
  const params = useParams();
  const router = useRouter();
  const sessionId = params?.id as string;
  
  const [sessionInfo, setSessionInfo] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchSessionAndQuestions = async () => {
    if (!token || !sessionId) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      
      // Fetch session info (mocked from questions or requires a real GET /sessions/:id endpoint)
      // Since we don't have GET /sessions/:id without course_id easily, we might just load questions.
      // Assuming we need session title, we might have passed it or we need a new endpoint. 
      // For now, let's just fetch questions and course might be fetched later.

      const qRes = await fetch(`${apiUrl}/questions?session_id=${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
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
    
    // Poll every 10 seconds for updates
    const interval = setInterval(fetchSessionAndQuestions, 10000);
    return () => clearInterval(interval);
  }, [token, sessionId]);

  const handleStatusChange = async (newStatus: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${apiUrl}/sessions/${sessionId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        // Optimistic update
        setSessionInfo({ ...sessionInfo, status: newStatus });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAction = async (action: 'claim' | 'resolve' | 'defer' | 'withdraw', questionId: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const body = action === 'resolve' ? { resolution_note: 'Resolved by TA' } : {};
      
      const res = await fetch(`${apiUrl}/questions/${questionId}/${action}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined
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

  const isStaff = user?.role === 'professor' || user?.role === 'ta';
  
  // Student view logic
  const activeQuestion = questions.find(q => ['queued', 'in_progress'].includes(q.status));

  // TA Queue view logic
  const queue = questions.filter(q => ['queued', 'in_progress'].includes(q.status)).sort((a, b) => a.queue_position - b.queue_position);

  return (
    <div className="min-h-screen bg-bg">
      <NavBar />
      
      <main className="max-w-5xl mx-auto p-6 md:p-8">
        <div className="mb-6">
           <button onClick={() => router.back()} className="inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        </div>
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b border-border pb-6">
          <div>
            <h1 className="text-3xl font-bold text-text-primary mb-2">Office Hours Session</h1>
            <p className="text-text-secondary">Manage the queue and assist students</p>
          </div>
          
          {user?.role === 'professor' && (
            <div className="flex gap-3">
              <button 
                onClick={() => handleStatusChange('active')}
                className="flex items-center gap-2 bg-green/10 text-green border border-green/20 hover:bg-green/20 px-4 py-2 rounded-input font-medium transition-colors"
                title="Start Session"
              >
                <Play className="w-4 h-4" /> Start
              </button>
              <button 
                onClick={() => handleStatusChange('ended')}
                className="flex items-center gap-2 bg-red/10 text-red border border-red/20 hover:bg-red/20 px-4 py-2 rounded-input font-medium transition-colors"
                title="End Session"
              >
                <Square className="w-4 h-4" /> End
              </button>
            </div>
          )}
        </div>

        {!isStaff ? (
          <div className="py-4">
            <QuestionSubmissionForm 
              sessionId={sessionId} 
              onSuccess={fetchSessionAndQuestions} 
              activeQuestion={activeQuestion}
              onWithdraw={(id) => handleAction('withdraw', id)}
            />
          </div>
        ) : (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <h2 className="text-xl font-bold text-text-primary">Live Queue</h2>
              <span className="bg-accent/20 text-accent px-3 py-1 rounded-full text-sm font-bold">{queue.length} Active</span>
            </div>
            
            {queue.length === 0 ? (
              <div className="bg-surface border border-border rounded-card p-12 text-center shadow-sm">
                <MessageSquare className="w-12 h-12 text-text-muted mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium text-text-primary mb-2">Queue is empty</h3>
                <p className="text-text-secondary">Students haven't submitted any questions yet.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {queue.map((q) => (
                  <div key={q.id} className={`bg-card border rounded-card p-5 shadow-sm transition-all ${q.status === 'in_progress' ? 'border-accent shadow-accent/10' : 'border-border hover:border-text-muted hover:shadow-md'}`}>
                    <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
                      <div className="bg-surface text-text-primary px-4 py-3 rounded-input text-center min-w-[80px] border border-border/50 shrink-0">
                        <div className="text-xs text-text-secondary mb-1">POS</div>
                        <div className="text-2xl font-bold">{q.queue_position}</div>
                      </div>
                      
                      <div className="flex-grow">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-text-primary text-lg">{q.title}</h3>
                          {q.status === 'in_progress' && (
                            <span className="bg-amber/10 text-amber text-xs px-2 py-0.5 rounded border border-amber/20 flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" /> Claimed
                            </span>
                          )}
                        </div>
                        <p className="text-text-secondary text-sm mb-2">{q.student?.name} • <span className="text-text-muted">{q.category}</span></p>
                        <p className="text-sm text-text-primary line-clamp-2 bg-[#0D1117] p-2 rounded-md border border-border/50">{q.description}</p>
                      </div>

                      <div className="flex flex-row md:flex-col gap-2 shrink-0 md:w-32">
                        {q.status === 'queued' && (
                          <button 
                            onClick={() => handleAction('claim', q.id)}
                            className="w-full bg-accent hover:bg-accent/90 text-white px-3 py-2 rounded-input text-sm font-medium transition-colors"
                          >
                            Claim
                          </button>
                        )}
                        {q.status === 'in_progress' && q.claimed_by === user?.id && (
                          <button 
                            onClick={() => handleAction('resolve', q.id)}
                            className="w-full bg-green text-white hover:bg-green/90 px-3 py-2 rounded-input text-sm font-medium transition-colors"
                          >
                            Resolve
                          </button>
                        )}
                        {q.status === 'queued' && (
                          <button 
                            onClick={() => handleAction('defer', q.id)}
                            className="w-full bg-surface border border-border hover:bg-surface/80 text-text-secondary px-3 py-2 rounded-input text-sm font-medium transition-colors"
                          >
                            Defer (Re-queue)
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

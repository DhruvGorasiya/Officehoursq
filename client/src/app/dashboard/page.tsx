'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import NavBar from '@/components/common/NavBar';
import { Plus } from 'lucide-react';
import Link from 'next/link';

interface Course {
  id: string;
  name: string;
  invite_code: string;
  professor_id: string;
  created_at: string;
}

export default function Dashboard() {
  const { user, token } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [courseName, setCourseName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');

  const fetchCourses = async () => {
    if (!token) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiUrl}/courses`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      if (data.success) {
        setCourses(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch courses');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, [token]);

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiUrl}/courses`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ name: courseName })
      });
      const data = await response.json();
      if (data.success) {
        setCourses([...courses, data.data]);
        setShowCreateModal(false);
        setCourseName('');
      } else {
        setError(data.message || 'Failed to create course');
      }
    } catch (err) {
      setError('Network error occurred');
    }
  };

  const handleJoinCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiUrl}/courses/join`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ invite_code: inviteCode.trim().toUpperCase() })
      });
      const data = await response.json();
      if (data.success) {
        fetchCourses();
        setShowJoinModal(false);
        setInviteCode('');
      } else {
        setError(data.message || 'Failed to join course');
      }
    } catch (err) {
      setError('Network error occurred');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg">
        <NavBar />
        <div className="p-8 text-center text-text-secondary">Loading courses...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg">
      <NavBar />
      
      <main className="max-w-4xl mx-auto p-6 md:p-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-text-primary">Your Courses</h1>
          {user?.role === 'professor' ? (
            <button 
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-input font-medium transition-colors"
            >
              <Plus className="w-5 h-5" />
              Create Course
            </button>
          ) : (
            <button 
              onClick={() => setShowJoinModal(true)}
              className="flex items-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-input font-medium transition-colors"
            >
              <Plus className="w-5 h-5" />
              Join Course
            </button>
          )}
        </div>

        {courses.length === 0 ? (
          <div className="bg-surface border border-border rounded-card p-12 text-center shadow-sm">
            <h3 className="text-lg font-medium text-text-primary mb-2">No courses yet</h3>
            <p className="text-text-secondary">
              {user?.role === 'professor' ? 'Create your first course to get started.' : 'Join a course using an invite code provided by your professor.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <Link href={`/courses/${course.id}`} key={course.id}>
                <div className="bg-card hover:bg-surface border border-border rounded-card p-6 shadow-sm cursor-pointer transition-colors group h-full">
                  <h3 className="font-semibold text-text-primary text-lg mb-2 group-hover:text-accent transition-colors">{course.name}</h3>
                  {user?.role === 'professor' && (
                    <div className="mt-4 pt-4 border-t border-border">
                      <p className="text-sm text-text-muted">Invite Code</p>
                      <p className="font-mono bg-bg border border-border px-2 py-1 rounded inline-block text-accent mt-1 tracking-wider">{course.invite_code}</p>
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>

      {/* Create Course Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex flex-col items-center justify-center p-4 z-50">
          <div className="bg-card rounded-card border border-border p-6 w-full max-w-md shadow-xl">
            <h2 className="text-xl font-bold text-text-primary mb-4">Create New Course</h2>
            {error && <div className="text-red text-sm mb-4 bg-red/10 p-3 rounded-input">{error}</div>}
            <form onSubmit={handleCreateCourse}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-text-secondary mb-1">Course Name</label>
                <input 
                  type="text" 
                  value={courseName}
                  onChange={(e) => setCourseName(e.target.value)}
                  className="w-full bg-surface border border-border rounded-input px-4 py-2 text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  placeholder="e.g. CS 101: Intro to Programming"
                  required
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
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

      {/* Join Course Modal */}
      {showJoinModal && (
        <div className="fixed inset-0 bg-black/50 flex flex-col items-center justify-center p-4 z-50">
          <div className="bg-card rounded-card border border-border p-6 w-full max-w-md shadow-xl">
            <h2 className="text-xl font-bold text-text-primary mb-4">Join Course</h2>
            {error && <div className="text-red text-sm mb-4 bg-red/10 p-3 rounded-input">{error}</div>}
            <form onSubmit={handleJoinCourse}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-text-secondary mb-1">Invite Code</label>
                <input 
                  type="text" 
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  className="w-full bg-surface border border-border rounded-input px-4 py-2 text-text-primary font-mono focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent uppercase"
                  placeholder="6-character code"
                  maxLength={6}
                  required
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button 
                  type="button" 
                  onClick={() => setShowJoinModal(false)}
                  className="px-4 py-2 font-medium text-text-secondary hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="bg-accent text-white px-4 py-2 rounded-input font-medium hover:bg-accent/90 transition-colors"
                >
                  Join
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

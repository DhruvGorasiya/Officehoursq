-- OfficeHoursQ - Core Sprint 1 Schema
-- Extends 001_initial_schema.sql with sessions, session TA assignments, and questions.

-- Drop everything in correct dependency order (idempotent for local dev)
-- DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
-- DROP FUNCTION IF EXISTS public.handle_new_user();

-- DROP POLICY IF EXISTS "Questions are viewable by everyone" ON public.questions;
-- DROP POLICY IF EXISTS "Anyone can insert questions" ON public.questions;
-- DROP POLICY IF EXISTS "Anyone can update questions" ON public.questions;
-- DROP POLICY IF EXISTS "Anyone can delete questions" ON public.questions;
-- DROP POLICY IF EXISTS "Assignments are viewable by everyone" ON public.session_ta_assignments;
-- DROP POLICY IF EXISTS "Anyone can insert assignments" ON public.session_ta_assignments;
-- DROP POLICY IF EXISTS "Anyone can delete assignments" ON public.session_ta_assignments;
-- DROP POLICY IF EXISTS "Sessions are viewable by everyone" ON public.sessions;
-- DROP POLICY IF EXISTS "Anyone can insert sessions" ON public.sessions;
-- DROP POLICY IF EXISTS "Anyone can update sessions" ON public.sessions;
-- DROP POLICY IF EXISTS "Anyone can delete sessions" ON public.sessions;
-- DROP POLICY IF EXISTS "Users are viewable by everyone" ON public.users;
-- DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
-- DROP POLICY IF EXISTS "Anyone can insert users" ON public.users;
-- DROP POLICY IF EXISTS "Courses are viewable by everyone" ON public.courses;
-- DROP POLICY IF EXISTS "Anyone can insert courses" ON public.courses;
-- DROP POLICY IF EXISTS "Enrollments are viewable by everyone" ON public.course_enrollments;
-- DROP POLICY IF EXISTS "Anyone can insert enrollments" ON public.course_enrollments;

-- DROP TABLE IF EXISTS public.questions;
-- DROP TABLE IF EXISTS public.session_ta_assignments;
-- DROP TABLE IF EXISTS public.sessions;
-- DROP TABLE IF EXISTS public.course_enrollments;
-- DROP TABLE IF EXISTS public.courses;
-- DROP TABLE IF EXISTS public.users;

-- DROP TYPE IF EXISTS question_category;
-- DROP TYPE IF EXISTS question_priority;
-- DROP TYPE IF EXISTS question_status;
-- DROP TYPE IF EXISTS session_status;
-- DROP TYPE IF EXISTS enrollment_role;
-- DROP TYPE IF EXISTS user_role;

-- Enum types
CREATE TYPE user_role AS ENUM ('student', 'ta', 'professor');
CREATE TYPE enrollment_role AS ENUM ('student', 'ta');
CREATE TYPE session_status AS ENUM ('scheduled', 'active', 'ended');
CREATE TYPE question_status AS ENUM ('queued', 'in_progress', 'deferred', 'resolved', 'withdrawn');
CREATE TYPE question_priority AS ENUM ('low', 'medium', 'high');
CREATE TYPE question_category AS ENUM ('debugging', 'conceptual', 'setup', 'assignment', 'other');

-- Users table (no FK to auth.users; backend handles insert after Supabase Auth signup)
CREATE TABLE public.users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role user_role NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Courses table
CREATE TABLE public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    invite_code TEXT UNIQUE NOT NULL,
    professor_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Course Enrollments table
CREATE TABLE public.course_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role enrollment_role NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(course_id, user_id)
);

-- Sessions table
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status session_status NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Session TA Assignments table
CREATE TABLE public.session_ta_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.sessions(id) ON DELETE CASCADE,
    ta_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(session_id, ta_id)
);

-- Questions table
CREATE TABLE public.questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(2000) NOT NULL,
    code_snippet VARCHAR(5000),
    error_message VARCHAR(1000),
    what_tried VARCHAR(2000),
    category question_category NOT NULL,
    priority question_priority NOT NULL DEFAULT 'low',
    status question_status NOT NULL DEFAULT 'queued',
    queue_position INTEGER NOT NULL DEFAULT 0,
    claimed_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    resolution_note TEXT,
    claimed_at TIMESTAMP WITH TIME ZONE,
    deferred_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_ta_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;

-- Permissive RLS policies (backend handles authorization via JWT)
CREATE POLICY "Users are viewable by everyone" ON public.users FOR SELECT USING (true);
CREATE POLICY "Anyone can insert users" ON public.users FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update own profile" ON public.users FOR UPDATE USING (true);

CREATE POLICY "Courses are viewable by everyone" ON public.courses FOR SELECT USING (true);
CREATE POLICY "Anyone can insert courses" ON public.courses FOR INSERT WITH CHECK (true);

CREATE POLICY "Enrollments are viewable by everyone" ON public.course_enrollments FOR SELECT USING (true);
CREATE POLICY "Anyone can insert enrollments" ON public.course_enrollments FOR INSERT WITH CHECK (true);

CREATE POLICY "Sessions are viewable by everyone" ON public.sessions FOR SELECT USING (true);
CREATE POLICY "Anyone can insert sessions" ON public.sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update sessions" ON public.sessions FOR UPDATE USING (true);
CREATE POLICY "Anyone can delete sessions" ON public.sessions FOR DELETE USING (true);

CREATE POLICY "Assignments are viewable by everyone" ON public.session_ta_assignments FOR SELECT USING (true);
CREATE POLICY "Anyone can insert assignments" ON public.session_ta_assignments FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can delete assignments" ON public.session_ta_assignments FOR DELETE USING (true);

CREATE POLICY "Questions are viewable by everyone" ON public.questions FOR SELECT USING (true);
CREATE POLICY "Anyone can insert questions" ON public.questions FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update questions" ON public.questions FOR UPDATE USING (true);
CREATE POLICY "Anyone can delete questions" ON public.questions FOR DELETE USING (true);


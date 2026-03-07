-- OfficeHoursQ - Sprint 1 Core Schema Migration

-- Create custom enum types
CREATE TYPE session_status AS ENUM ('scheduled', 'active', 'ended');
CREATE TYPE question_status AS ENUM ('queued', 'in_progress', 'deferred', 'resolved', 'withdrawn');
CREATE TYPE question_priority AS ENUM ('low', 'medium', 'high');
CREATE TYPE question_category AS ENUM ('debugging', 'conceptual', 'setup', 'assignment', 'other');

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

-- Enable RLS
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_ta_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;

-- Permissive RLS policies (backend handles authorization via JWT)
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

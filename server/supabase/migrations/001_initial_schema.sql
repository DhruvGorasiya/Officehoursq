-- OfficeHoursQ - Initial Schema Migration (Sprint 1)
-- Requires Supabase PostgreSQL

-- Create custom enum types
CREATE TYPE user_role AS ENUM ('student', 'ta', 'professor');
CREATE TYPE enrollment_role AS ENUM ('student', 'ta');

-- Users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role user_role NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Courses table
CREATE TABLE IF NOT EXISTS public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    invite_code TEXT UNIQUE NOT NULL,
    professor_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- CourseEnrollments table
CREATE TABLE IF NOT EXISTS public.course_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role enrollment_role NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(course_id, user_id)
);

-- Enable RLS (Row Level Security)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_enrollments ENABLE ROW LEVEL SECURITY;

-- Basic RLS Policies (Sprint 1)
-- Users can see their own profile, professors can see profiles of enrolled students, etc.
-- For now, letting authenticated users see other users to enable basic app functionality.
CREATE POLICY "Users are viewable by everyone" ON public.users
    FOR SELECT USING (true);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Courses are viewable by everyone (to validate invite codes)
CREATE POLICY "Courses are viewable by everyone" ON public.courses
    FOR SELECT USING (true);

-- Only professors can create courses
CREATE POLICY "Professors can insert courses" ON public.courses
    FOR INSERT WITH CHECK (
        auth.uid() IN (SELECT id FROM public.users WHERE role = 'professor')
    );

-- Course enrollments are viewable by users in that course, and the professor of that course
CREATE POLICY "Enrollments viewable by enrolled users or professor" ON public.course_enrollments
    FOR SELECT USING (
        auth.uid() = user_id OR 
        auth.uid() IN (SELECT professor_id FROM public.courses WHERE id = course_id)
    );

-- Students/TAs can insert their own enrollments
CREATE POLICY "Users can enroll themselves" ON public.course_enrollments
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Setup Supabase Auth Trigger to automatically create a user record in public.users
-- Since role and name need to be passed during signup, we extract them from user metadata
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, name, role)
  VALUES (
    new.id, 
    new.email, 
    new.raw_user_meta_data->>'name', 
    CAST(new.raw_user_meta_data->>'role' AS user_role)
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to run handle_new_user on auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

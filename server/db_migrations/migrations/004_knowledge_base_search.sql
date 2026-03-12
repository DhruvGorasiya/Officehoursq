-- OfficeHoursQ - Knowledge Base Search Support
-- Adds course_id + helpful_votes to questions, creates helpful_votes table,
-- adds full-text search vector with GIN index, and an RPC for similar-question ranking.

-- 1. Add course_id to questions (nullable initially so we can backfill)
ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS course_id UUID REFERENCES public.courses(id) ON DELETE CASCADE;

-- Backfill course_id from the related session
UPDATE public.questions
SET course_id = s.course_id
FROM public.sessions s
WHERE public.questions.session_id = s.id
  AND public.questions.course_id IS NULL;

-- Now enforce NOT NULL
ALTER TABLE public.questions
    ALTER COLUMN course_id SET NOT NULL;

-- 2. Add helpful_votes counter
ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS helpful_votes INTEGER NOT NULL DEFAULT 0;

-- 3. Create helpful_votes table
CREATE TABLE IF NOT EXISTS public.helpful_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(question_id, student_id)
);

ALTER TABLE public.helpful_votes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Helpful votes are viewable by everyone"
    ON public.helpful_votes FOR SELECT USING (true);
CREATE POLICY "Anyone can insert helpful votes"
    ON public.helpful_votes FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can delete helpful votes"
    ON public.helpful_votes FOR DELETE USING (true);

-- 4. Full-text search vector (generated column over title + description + resolution_note)
ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(title, '') || ' ' ||
            coalesce(description, '') || ' ' ||
            coalesce(resolution_note, '')
        )
    ) STORED;

-- 5. Indexes
CREATE INDEX IF NOT EXISTS idx_questions_search_vector
    ON public.questions USING GIN (search_vector);

CREATE INDEX IF NOT EXISTS idx_questions_course_status
    ON public.questions (course_id, status);

-- 6. RPC: find_similar_questions
--    Returns top N resolved questions ranked by full-text relevance.
CREATE OR REPLACE FUNCTION public.find_similar_questions(
    p_course_id UUID,
    p_title TEXT,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    description VARCHAR,
    category question_category,
    resolution_note TEXT,
    helpful_votes INTEGER,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    student_name TEXT,
    rank REAL
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        q.id,
        q.title,
        q.description,
        q.category,
        q.resolution_note,
        q.helpful_votes,
        q.resolved_at,
        q.created_at,
        u.name AS student_name,
        ts_rank(q.search_vector, websearch_to_tsquery('english', p_title)) AS rank
    FROM public.questions q
    JOIN public.users u ON u.id = q.student_id
    WHERE q.course_id = p_course_id
      AND q.status = 'resolved'
      AND q.search_vector @@ websearch_to_tsquery('english', p_title)
    ORDER BY rank DESC, q.helpful_votes DESC, q.resolved_at DESC
    LIMIT p_limit;
END;
$$;

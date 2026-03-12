-- Seed data for CS5432 – AI-assisted Coding
-- Professor: 43e2af59-4ba7-4791-bb96-c1d45cb15f07
-- TA:        f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702
-- Student:   f7f85786-3ad1-4d2d-b138-5ac72fa62206

BEGIN;

-- Course
INSERT INTO public.courses (id, name, invite_code, professor_id)
VALUES (
  '11111111-2222-4333-8444-555555555555',
  'CS5432 – AI-assisted Coding',
  'AI4DEV',
  '43e2af59-4ba7-4791-bb96-c1d45cb15f07'
) ON CONFLICT (id) DO NOTHING;

-- Enrollments
INSERT INTO public.course_enrollments (id, course_id, user_id, role, joined_at) VALUES
  ('55555555-6666-4777-8888-999999999999', '11111111-2222-4333-8444-555555555555', 'f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702', 'ta',      NOW() - INTERVAL '5 days'),
  ('66666666-7777-4888-9999-000000000000', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206', 'student', NOW() - INTERVAL '4 days')
ON CONFLICT (id) DO NOTHING;

-- Sessions
INSERT INTO public.sessions (id, course_id, title, date, start_time, end_time, status, created_at) VALUES
  ('22222222-3333-4444-8555-666666666666', '11111111-2222-4333-8444-555555555555', 'Week 1 – Getting Started with AI Tools',   CURRENT_DATE - INTERVAL '7 days', '17:00', '19:00', 'ended',     NOW() - INTERVAL '8 days'),
  ('33333333-4444-4555-8666-777777777777', '11111111-2222-4333-8444-555555555555', 'Week 2 – Debugging with AI Assistance',    CURRENT_DATE,                     '17:00', '19:00', 'active',    NOW() - INTERVAL '2 days'),
  ('44444444-5555-4666-8777-888888888888', '11111111-2222-4333-8444-555555555555', 'Week 3 – Refactoring Legacy Code with AI', CURRENT_DATE + INTERVAL '4 days', '17:00', '19:00', 'scheduled', NOW())
ON CONFLICT (id) DO NOTHING;

-- TA Assignments
INSERT INTO public.session_ta_assignments (id, session_id, ta_id, created_at) VALUES
  ('77777777-8888-4999-9000-aaaaaaaaaaaa', '22222222-3333-4444-8555-666666666666', 'f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702', NOW() - INTERVAL '7 days'),
  ('88888888-9999-4aaa-a111-bbbbbbbbbbbb', '33333333-4444-4555-8666-777777777777', 'f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702', NOW() - INTERVAL '2 days'),
  ('99999999-aaaa-4bbb-b222-cccccccccccc', '44444444-5555-4666-8777-888888888888', 'f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702', NOW())
ON CONFLICT (id) DO NOTHING;

-- Questions: Week 2 (active session)
INSERT INTO public.questions (
  id, session_id, course_id, student_id, title, description, code_snippet, error_message,
  what_tried, category, priority, status, queue_position,
  claimed_by, resolution_note, claimed_at, deferred_at, resolved_at, created_at
) VALUES
(
  'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeee1',
  '33333333-4444-4555-8666-777777777777', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'Unit tests failing after AI-suggested refactor',
  'I asked an AI tool to refactor my repository service. The code compiles, but my pytest suite now fails on the user permissions tests. I''m not sure which behavior changed compared to the original implementation.',
  'def can_edit_repo(user, repo):\n    if user.is_admin:\n        return True\n    # AI suggested collapsing these checks\n    return repo.owner_id == user.id or user.id in repo.collaborator_ids\n',
  'E AssertionError: expected False, got True for anonymous user on private repo',
  'I compared the old and new implementations and printed the inputs inside the failing tests. I also asked the AI to explain the diff, but the explanation didn''t mention the anonymous-user case.',
  'debugging', 'high', 'in_progress', 1,
  'f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702', NULL, NOW() - INTERVAL '15 minutes', NULL, NULL, NOW() - INTERVAL '40 minutes'
),
(
  'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeee2',
  '33333333-4444-4555-8666-777777777777', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'Chat completion client hanging on network errors',
  'I''m building a small CLI that calls an AI coding assistant. Sometimes the command just hangs when the network drops instead of timing out and retrying. I want to make sure I''m handling cancellations and timeouts correctly.',
  'async def complete(prompt: str) -> str:\n    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:\n        async with session.post(API_URL, json={"prompt": prompt}) as resp:\n            return await resp.text()\n',
  'No error, just hangs forever on bad Wi-Fi. Ctrl+C cancels it.',
  'I added a timeout to the client and wrapped the call in asyncio.wait_for, but the behavior didn''t change much. I also asked an AI to suggest retry logic and implemented exponential backoff, but I think I''m missing proper cancellation.',
  'debugging', 'high', 'queued', 2,
  NULL, NULL, NULL, NULL, NULL, NOW() - INTERVAL '35 minutes'
),
(
  'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeee3',
  '33333333-4444-4555-8666-777777777777', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'How much should I trust AI-generated type hints?',
  'For the final project we''re required to have good type coverage. I used an AI assistant to add a bunch of TypeScript types to my React code. Some of them feel overly generic (any/unknown) and I''m not sure when I should tighten them vs leave them as-is.',
  'type ApiResponse = any;\n\nasync function fetchUser(id: string): Promise<ApiResponse> {\n  const res = await fetch(`/api/users/${id}`);\n  return res.json();\n}\n',
  NULL,
  'I read the course notes on soundness and watched the lecture on type inference again. I also asked the AI to ''make the types stricter'' but it sometimes breaks the build.',
  'conceptual', 'medium', 'queued', 3,
  NULL, NULL, NULL, NULL, NULL, NOW() - INTERVAL '30 minutes'
),
(
  'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeee4',
  '33333333-4444-4555-8666-777777777777', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'VS Code AI extension not respecting virtualenv',
  'The AI code completion extension in VS Code keeps suggesting imports from the global Python installation instead of my project''s venv. This causes it to recommend packages we are not allowed to use in the assignment.',
  NULL, NULL,
  'I re-created the virtualenv, set the Python interpreter to the venv in VS Code, and restarted the editor. I also searched the extension docs but didn''t find anything about respecting the venv.',
  'setup', 'low', 'queued', 4,
  NULL, NULL, NULL, NULL, NULL, NOW() - INTERVAL '25 minutes'
),
(
  'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeee5',
  '33333333-4444-4555-8666-777777777777', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'Refactoring AI-generated helper into smaller functions',
  'For the lab, I asked an AI to generate a helper that scores code review comments. The function is very long and hard to test. I want to refactor it into smaller pieces without changing behavior.',
  'function scoreComment(comment: string): number {\n  // 60+ lines of AI-generated heuristics ...\n}\n',
  NULL,
  'I highlighted the function and asked the AI to ''split this into smaller pure helpers''. It produced something, but I don''t know how to evaluate whether the new structure is actually better or easier to test.',
  'assignment', 'medium', 'deferred', 5,
  NULL, NULL, NULL, NOW() - INTERVAL '20 minutes', NULL, NOW() - INTERVAL '50 minutes'
),
(
  'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeee6',
  '33333333-4444-4555-8666-777777777777', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'Prompt for getting minimal diff from AI',
  'I want to ask an AI assistant to propose the smallest possible change to fix a failing test instead of rewriting the whole file. Looking for feedback on good prompt patterns.',
  NULL, NULL,
  'I tried prompts like "only return the changed lines" and "respond with a unified diff", but the assistant occasionally rewrites unrelated parts.',
  'other', 'low', 'resolved', -1,
  'f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702', 'Discussed concrete prompt templates and how to lock context to a single function.',
  NOW() - INTERVAL '1 hour', NULL, NOW() - INTERVAL '50 minutes', NOW() - INTERVAL '2 hours'
),
(
  'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeee7',
  '33333333-4444-4555-8666-777777777777', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'AI-generated SQL query timing out on large table',
  'The AI wrote a SELECT with multiple joins for the analytics part of the project. It works in the staging database but times out on the production-sized dataset. I wanted to know how to spot obvious performance issues in AI-generated SQL.',
  'SELECT u.id, COUNT(q.id) AS question_count\nFROM users u\nJOIN questions q ON q.student_id = u.id\nWHERE q.created_at > NOW() - INTERVAL ''30 days''\nGROUP BY u.id\nORDER BY question_count DESC;\n',
  NULL,
  'I tried adding indexes on created_at and student_id and asked the AI for an "optimized version" of the query. It suggested some changes but I don''t fully understand the tradeoffs.',
  'debugging', 'medium', 'resolved', -1,
  'f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702', 'Reviewed EXPLAIN output and suggested a better index strategy and WHERE clause.',
  NOW() - INTERVAL '90 minutes', NULL, NOW() - INTERVAL '70 minutes', NOW() - INTERVAL '3 hours'
)
ON CONFLICT (id) DO NOTHING;

-- Questions: Week 1 (ended session)
INSERT INTO public.questions (
  id, session_id, course_id, student_id, title, description, code_snippet, error_message,
  what_tried, category, priority, status, queue_position,
  claimed_by, resolution_note, claimed_at, deferred_at, resolved_at, created_at
) VALUES
(
  'bbbbbbbb-cccc-4ddd-8eee-fffffffffff1',
  '22222222-3333-4444-8555-666666666666', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'Choosing between different AI-assisted workflows for this course',
  'I''m trying to decide whether to use the IDE plugin or the web-based chat UI for coding in this course. I want to make sure I respect the academic integrity guidelines.',
  NULL, NULL,
  'I read the course policy and asked an AI to summarize it, but I''d like a human sanity check on my understanding.',
  'conceptual', 'low', 'resolved', -1,
  'f894afbe-b18a-4bc8-a2e9-eb9f4a9fd702', 'Clarified when AI assistance is allowed and how to document usage in the README.',
  (CURRENT_TIMESTAMP - INTERVAL '7 days') + INTERVAL '70 minutes',
  NULL,
  (CURRENT_TIMESTAMP - INTERVAL '7 days') + INTERVAL '90 minutes',
  (CURRENT_TIMESTAMP - INTERVAL '7 days') + INTERVAL '30 minutes'
),
(
  'bbbbbbbb-cccc-4ddd-8eee-fffffffffff2',
  '22222222-3333-4444-8555-666666666666', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'Setting up a safe sandbox for AI-generated code',
  'For homework 1 we''re supposed to run AI-generated code only in a sandbox. I''m not sure what minimum isolation is considered safe on my laptop.',
  NULL, NULL,
  'I looked at Docker and VS Code devcontainers and asked an AI how to set them up, but I still don''t know what is "good enough".',
  'setup', 'medium', 'unresolved', -1,
  NULL, 'Session ended without resolution',
  NULL, NULL, NULL,
  (CURRENT_TIMESTAMP - INTERVAL '7 days') + INTERVAL '40 minutes'
),
(
  'bbbbbbbb-cccc-4ddd-8eee-fffffffffff3',
  '22222222-3333-4444-8555-666666666666', '11111111-2222-4333-8444-555555555555', 'f7f85786-3ad1-4d2d-b138-5ac72fa62206',
  'Licensing concerns for AI-suggested code snippets',
  'During the first week I pasted some AI-suggested code into my project. I later learned that some models might reproduce licensed material. I want to know if I need to rewrite that code.',
  NULL, NULL,
  'I searched the documentation of the provider and asked the AI directly about licensing, but the answers were vague.',
  'conceptual', 'high', 'unresolved', -1,
  NULL, 'Session ended without resolution',
  NULL, NULL, NULL,
  (CURRENT_TIMESTAMP - INTERVAL '7 days') + INTERVAL '45 minutes'
)
ON CONFLICT (id) DO NOTHING;

COMMIT;
-- OfficeHoursQ - Add 'unresolved' to question_status enum
-- Used when a session ends and queued/in_progress/deferred questions remain.

ALTER TYPE question_status ADD VALUE 'unresolved';

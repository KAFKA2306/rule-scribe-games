BEGIN;

-- Migration 006 already blocks new NULL/blank slugs with a NOT VALID check.
-- Production legacy reconciliation has reduced existing violations to zero, so
-- validation can now promote the invariant without changing application code.
ALTER TABLE public.games VALIDATE CONSTRAINT games_slug_required;

COMMIT;

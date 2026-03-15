-- Migration: Add rules_summary column to games table
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/_/sql

ALTER TABLE games ADD COLUMN IF NOT EXISTS rules_summary TEXT;

-- Verify the column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'games' AND column_name = 'rules_summary';

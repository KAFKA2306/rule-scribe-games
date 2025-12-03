-- Migration script for existing databases
-- Run this in Supabase SQL Editor for production database

-- Add missing columns
alter table games add column if not exists slug text;
alter table games add column if not exists summary text;
alter table games add column if not exists structured_data jsonb default '{}'::jsonb;

-- Generate slug values for existing records
update games 
set slug = lower(regexp_replace(title, '[^a-zA-Z0-9]+', '-', 'g'))
where slug is null or slug = '';

-- Add unique constraint to slug after populating values
alter table games add constraint games_slug_unique unique (slug);

-- Create indexes for better query performance
create index if not exists idx_games_slug on games(slug);
create index if not exists idx_games_title on games(title);

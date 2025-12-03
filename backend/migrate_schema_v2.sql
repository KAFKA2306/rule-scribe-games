-- Migration script v2
-- Run this in Supabase SQL Editor

-- 1. Fix updated_at trigger reliability
-- Enable the extension if available
create extension if not exists moddatetime schema extensions;

-- Drop the old trigger to replace it
drop trigger if exists update_games_updated_at on games;

-- Create the new trigger using the standard extension
-- If moddatetime is not available, the previous custom function remains but trigger is dropped.
-- Ideally, we use moddatetime.
create trigger handle_updated_at before update on games
  for each row execute procedure moddatetime (updated_at);

-- 2. Add Missing Columns for Analytics & Logic
alter table games add column if not exists view_count bigint default 0;
alter table games add column if not exists search_count bigint default 0;
alter table games add column if not exists data_version integer default 0;
alter table games add column if not exists is_official boolean default false;

-- 3. Add Columns for Sorting/Filtering (Metadata) (#28)
alter table games add column if not exists min_players integer;
alter table games add column if not exists max_players integer;
alter table games add column if not exists play_time integer;
alter table games add column if not exists min_age integer;
alter table games add column if not exists published_year integer;

-- 4. Add Columns for Titles (#28)
alter table games add column if not exists title_ja text;
alter table games add column if not exists title_en text;

-- 5. Add Columns for External Links (#31, #33)
alter table games add column if not exists official_url text;
alter table games add column if not exists bgg_url text;
alter table games add column if not exists bga_url text;
alter table games add column if not exists amazon_url text;

-- 6. Add Columns for Media/Content (#30, #32)
alter table games add column if not exists audio_url text;
-- Note: image_url already exists. Additional images can be stored in structured_data or a new table if needed.

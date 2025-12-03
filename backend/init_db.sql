-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;
create extension if not exists moddatetime schema extensions;

create table if not exists games (
  id bigint primary key generated always as identity,
  slug text unique not null,
  title text not null,
  description text,
  summary text,
  rules_content text,
  source_url text unique,
  image_url text,
  structured_data jsonb default '{}'::jsonb,

  -- Analytics & Logic
  view_count bigint default 0,
  search_count bigint default 0,
  data_version integer default 0,
  is_official boolean default false,

  -- Metadata for Sorting/Filtering (#28)
  min_players integer,
  max_players integer,
  play_time integer,
  min_age integer,
  published_year integer,

  -- Titles (#28)
  title_ja text,
  title_en text,

  -- External Links (#31, #33)
  official_url text,
  bgg_url text,
  bga_url text,
  amazon_url text,

  -- Media/Content (#30, #32)
  audio_url text,

  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create index if not exists idx_games_slug on games(slug);
create index if not exists idx_games_title on games(title);

-- Create a trigger to automatically update updated_at using moddatetime
create trigger handle_updated_at before update on games
  for each row execute procedure moddatetime (updated_at);

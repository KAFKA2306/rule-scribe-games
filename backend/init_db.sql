-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

create table if not exists games (
  id bigint primary key generated always as identity,
  slug text unique not null,
  title text not null,
  slug text unique not null,
  description text,
  summary text,
  rules_content text,
  structured_data jsonb default '{}'::jsonb,
  source_url text unique,
  image_url text,
  structured_data jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create index if not exists idx_games_slug on games(slug);
create index if not exists idx_games_title on games(title);

-- Create a function to update the updated_at column
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Create a trigger to automatically update updated_at
create trigger update_games_updated_at
before update on games
for each row
execute function update_updated_at_column();

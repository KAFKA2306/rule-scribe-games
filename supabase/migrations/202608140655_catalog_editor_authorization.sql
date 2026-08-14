create table if not exists public.catalog_editors (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null check (role in ('owner', 'editor')),
  active boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.catalog_editors enable row level security;

create table if not exists public.catalog_mutation_audit (
  id bigint generated always as identity primary key,
  actor_user_id uuid not null references auth.users(id) on delete restrict,
  game_slug text not null,
  action text not null check (action in ('manual_update', 'regenerate')),
  changed_fields text[] not null default '{}',
  outcome text not null check (outcome in ('allowed', 'denied', 'succeeded', 'not_found', 'failed')),
  created_at timestamptz not null default now()
);

alter table public.catalog_mutation_audit enable row level security;

create index if not exists catalog_mutation_audit_actor_created_idx
  on public.catalog_mutation_audit(actor_user_id, created_at desc);
create index if not exists catalog_mutation_audit_game_created_idx
  on public.catalog_mutation_audit(game_slug, created_at desc);

alter table public.games enable row level security;

drop policy if exists games_public_read on public.games;
create policy games_public_read
  on public.games
  for select
  to anon, authenticated
  using (true);

revoke insert, update, delete, truncate, references, trigger on table public.games from anon, authenticated;
grant select on table public.games to anon, authenticated;

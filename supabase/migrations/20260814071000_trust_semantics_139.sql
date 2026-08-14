alter table public.games
  add column if not exists source_trust_status text not null default 'unknown',
  add column if not exists content_review_status text not null default 'ai_draft';

update public.games
set source_trust_status = case
  when exists (
    select 1
    from jsonb_array_elements(coalesce(structured_data->'source_documents', '[]'::jsonb)) as doc
    where doc->>'type' in ('publisher_official', 'publisher_official_faq')
  ) then 'publisher_primary'
  when exists (
    select 1
    from jsonb_array_elements(coalesce(structured_data->'source_documents', '[]'::jsonb)) as doc
    where doc->>'type' in (
      'platform_official_rules',
      'platform_official_game',
      'platform_official_game_page',
      'platform_rules_summary'
    )
  ) then 'platform_primary'
  else 'unknown'
end;

update public.games
set content_review_status = case
  when structured_data->'generation_provenance'->>'content_review_status' in (
    'ai_draft',
    'human_reviewed',
    'publisher_reviewed'
  ) then structured_data->'generation_provenance'->>'content_review_status'
  else 'ai_draft'
end;

update public.games
set is_official = false
where is_official is true
  and identity_status <> 'verified';

alter table public.games
  drop constraint if exists games_source_trust_status_check,
  add constraint games_source_trust_status_check
    check (source_trust_status in ('unknown', 'publisher_primary', 'platform_primary', 'secondary', 'tertiary')),
  drop constraint if exists games_content_review_status_check,
  add constraint games_content_review_status_check
    check (content_review_status in ('ai_draft', 'human_reviewed', 'publisher_reviewed')),
  drop constraint if exists games_legacy_official_requires_verified_identity_check,
  add constraint games_legacy_official_requires_verified_identity_check
    check (not coalesce(is_official, false) or identity_status = 'verified');

comment on column public.games.source_trust_status is
  'Trust level of explicit source provenance. Independent from identity_status and legacy is_official.';

comment on column public.games.content_review_status is
  'Review state of game content. Independent from source_trust_status and identity_status.';

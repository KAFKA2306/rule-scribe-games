-- Harden public function execution boundaries reported by Supabase security advisor.
-- Keep existing triggers and fail-closed RLS behavior unchanged.

begin;

-- SECURITY DEFINER auth trigger helper must not be directly callable by browser roles.
revoke execute on function public.handle_new_user() from public, anon, authenticated;
grant execute on function public.handle_new_user() to service_role;

-- Trigger / normalization helpers should resolve built-ins deterministically instead
-- of inheriting a caller-controlled search_path.
alter function public.update_updated_at_column() set search_path = '';
alter function public.normalize_game_title(text) set search_path = '';
alter function public.protect_and_capture_game_slug() set search_path = '';

commit;

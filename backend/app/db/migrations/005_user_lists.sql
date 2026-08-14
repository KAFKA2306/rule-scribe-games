BEGIN;

CREATE TABLE public.user_lists (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  name text NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 80),
  visibility text NOT NULL DEFAULT 'private' CHECK (visibility IN ('private', 'public')),
  system_key text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX user_lists_owner_system_key_unique
  ON public.user_lists(owner_id, system_key)
  WHERE system_key IS NOT NULL;
CREATE INDEX user_lists_owner_created_idx
  ON public.user_lists(owner_id, created_at DESC);

CREATE TABLE public.user_list_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  list_id uuid NOT NULL REFERENCES public.user_lists(id) ON DELETE CASCADE,
  game_id uuid REFERENCES public.games(id) ON DELETE SET NULL,
  game_title_snapshot text NOT NULL CHECK (length(trim(game_title_snapshot)) > 0),
  position integer NOT NULL DEFAULT 0 CHECK (position >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX user_list_items_list_game_unique
  ON public.user_list_items(list_id, game_id)
  WHERE game_id IS NOT NULL;
CREATE INDEX user_list_items_list_position_idx
  ON public.user_list_items(list_id, position, created_at);

ALTER TABLE public.user_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_list_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_lists_select_own ON public.user_lists
  FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = owner_id);
CREATE POLICY user_lists_insert_own ON public.user_lists
  FOR INSERT TO authenticated
  WITH CHECK ((SELECT auth.uid()) = owner_id);
CREATE POLICY user_lists_update_own ON public.user_lists
  FOR UPDATE TO authenticated
  USING ((SELECT auth.uid()) = owner_id)
  WITH CHECK ((SELECT auth.uid()) = owner_id);
CREATE POLICY user_lists_delete_own ON public.user_lists
  FOR DELETE TO authenticated
  USING ((SELECT auth.uid()) = owner_id);

CREATE POLICY user_list_items_select_own ON public.user_list_items
  FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.user_lists l
    WHERE l.id = user_list_items.list_id
      AND l.owner_id = (SELECT auth.uid())
  ));
CREATE POLICY user_list_items_insert_own ON public.user_list_items
  FOR INSERT TO authenticated
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.user_lists l
    WHERE l.id = user_list_items.list_id
      AND l.owner_id = (SELECT auth.uid())
  ));
CREATE POLICY user_list_items_update_own ON public.user_list_items
  FOR UPDATE TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.user_lists l
    WHERE l.id = user_list_items.list_id
      AND l.owner_id = (SELECT auth.uid())
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.user_lists l
    WHERE l.id = user_list_items.list_id
      AND l.owner_id = (SELECT auth.uid())
  ));
CREATE POLICY user_list_items_delete_own ON public.user_list_items
  FOR DELETE TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.user_lists l
    WHERE l.id = user_list_items.list_id
      AND l.owner_id = (SELECT auth.uid())
  ));

REVOKE ALL PRIVILEGES ON TABLE public.user_lists FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.user_list_items FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.user_lists TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.user_list_items TO authenticated;
GRANT ALL PRIVILEGES ON TABLE public.user_lists TO service_role;
GRANT ALL PRIVILEGES ON TABLE public.user_list_items TO service_role;

CREATE OR REPLACE FUNCTION public.reorder_owned_list_items(
  p_owner_id uuid,
  p_list_id uuid,
  p_item_ids uuid[]
)
RETURNS void
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
  expected_count integer;
  supplied_count integer;
  supplied_distinct integer;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.user_lists
    WHERE id = p_list_id AND owner_id = p_owner_id
  ) THEN
    RAISE EXCEPTION 'list_not_found' USING ERRCODE = 'P0002';
  END IF;

  SELECT count(*) INTO expected_count
  FROM public.user_list_items
  WHERE list_id = p_list_id;

  supplied_count := COALESCE(cardinality(p_item_ids), 0);
  SELECT count(DISTINCT item_id) INTO supplied_distinct
  FROM unnest(COALESCE(p_item_ids, ARRAY[]::uuid[])) AS item_id;

  IF supplied_count <> expected_count OR supplied_distinct <> expected_count THEN
    RAISE EXCEPTION 'invalid_item_order' USING ERRCODE = '22023';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM unnest(COALESCE(p_item_ids, ARRAY[]::uuid[])) AS supplied(item_id)
    LEFT JOIN public.user_list_items li
      ON li.id = supplied.item_id AND li.list_id = p_list_id
    WHERE li.id IS NULL
  ) THEN
    RAISE EXCEPTION 'invalid_item_order' USING ERRCODE = '22023';
  END IF;

  UPDATE public.user_list_items li
  SET position = ordered.ordinality - 1,
      updated_at = now()
  FROM unnest(COALESCE(p_item_ids, ARRAY[]::uuid[])) WITH ORDINALITY AS ordered(item_id, ordinality)
  WHERE li.id = ordered.item_id AND li.list_id = p_list_id;

  UPDATE public.user_lists
  SET updated_at = now()
  WHERE id = p_list_id AND owner_id = p_owner_id;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.reorder_owned_list_items(uuid, uuid, uuid[]) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.reorder_owned_list_items(uuid, uuid, uuid[]) FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION public.reorder_owned_list_items(uuid, uuid, uuid[]) TO service_role;

COMMIT;

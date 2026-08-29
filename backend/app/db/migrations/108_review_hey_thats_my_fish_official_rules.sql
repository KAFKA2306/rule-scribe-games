BEGIN;

-- プレイヤー向け成功条件:
-- 「それはオレの魚だ！」が、現在の Next Move Games 公式商品ページと
-- © 2023 Plan B Games Inc. 公式ルールブックだけをルール根拠として、
-- 準備 → 手番 → 動けない場合 → 終了 → 勝敗まで説明でき、検索公開されること。
-- 旧来の出典なし rules_content は公開ルールauthorityとして残さない。

INSERT INTO public.evidence_sources
  (source_id, url, document_identity, source_type, publisher_name, platform, language_code,
   revision_label, retrieved_at, trust_metadata)
VALUES
  ('publisher:nextmove:hey-thats-my-fish:product-en',
   'https://www.nextmove-games.com/en/hey-thats-my-fish/',
   'Hey That''s My Fish! — Next Move Games product page',
   'publisher_product_page', 'Next Move Games', 'physical', 'en',
   'current-accessed-2026-08-29', now(),
   '{"trust":"official_publisher","use":"identity_and_metadata"}'::jsonb),
  ('publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',
   'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf',
   'Hey, that''s my fish! Rulebook — © 2023 Plan B Games Inc.',
   'publisher_rulebook', 'Plan B Games Inc.', 'physical', 'en',
   'copyright-2023', now(),
   '{"trust":"official_publisher","linked_from":"https://www.nextmove-games.com/en/hey-thats-my-fish/"}'::jsonb),
  ('publisher:arclight:hey-thats-my-fish:2026-product-ja',
   'https://arclightgames.jp/product/659hau/',
   'それはオレの魚だ！ — ArclightGames Official',
   'publisher_product_page', 'アークライト', 'physical', 'ja',
   '2026-release-planned-accessed-2026-08-29', now(),
   '{"trust":"official_local_publisher","use":"japanese_title_and_local_product_metadata","release_status":"planned"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url = EXCLUDED.url,
  document_identity = EXCLUDED.document_identity,
  source_type = EXCLUDED.source_type,
  publisher_name = EXCLUDED.publisher_name,
  platform = EXCLUDED.platform,
  language_code = EXCLUDED.language_code,
  revision_label = EXCLUDED.revision_label,
  retrieved_at = EXCLUDED.retrieved_at,
  trust_metadata = EXCLUDED.trust_metadata,
  updated_at = now();

INSERT INTO public.source_locators
  (locator_id, source_id, page_number, section_heading, external_reference)
VALUES
  ('hey-thats-my-fish:setup-board','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',1,'Setup','Setup steps 1–2'),
  ('hey-thats-my-fish:setup-penguins','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',1,'Setup','Setup step 3 — penguin counts and placement'),
  ('hey-thats-my-fish:turn-order','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',2,'Playing the game','Beginning player and clockwise turn order'),
  ('hey-thats-my-fish:move-penguin','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',2,'Playing the game — Move one penguin','Six hex directions and movement restrictions'),
  ('hey-thats-my-fish:collect-floe','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',2,'Playing the game — Collect one ice floe tile','Collect the starting floe'),
  ('hey-thats-my-fish:unable-to-move','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',2,'Playing the game','Unable to move any penguin'),
  ('hey-thats-my-fish:end-game','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',2,'End of the game','All penguins removed'),
  ('hey-thats-my-fish:victory','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en',2,'End of the game','Most fish and tie breakers')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
  page_number = EXCLUDED.page_number,
  section_heading = EXCLUDED.section_heading,
  external_reference = EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_work_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id, work_id INTO v_game_id, v_work_id
  FROM public.games WHERE slug = 'hey-thats-my-fish' LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Hey That''s My Fish canonical game row is not part of the fixture; skipping migration';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical hey-thats-my-fish game row is required';
  END IF;

  SELECT count(*) INTO v_count FROM public.rule_sets WHERE game_id = v_game_id;
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'hey-thats-my-fish expected 0 existing RuleSets before migration, found %', v_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.games
    WHERE id = v_game_id
      AND amazon_url LIKE '%tag=bodogemikata-22%'
      AND identity_status = 'unverified'
      AND content_review_status IN ('unknown','review_required')
  ) THEN
    RAISE EXCEPTION 'hey-thats-my-fish pre-migration state changed; re-audit before publishing';
  END IF;

  INSERT INTO public.rule_sets
    (game_id, work_id, version, schema_version, language_code, source_revision, is_active,
     revision_label, platform, publisher_name, status, verification_status, source_ids)
  VALUES
    (v_game_id, v_work_id, 1, '1.0', 'ja',
     '© 2023 Plan B Games Inc. official rulebook linked from current Next Move Games product page',
     true, 'copyright-2023', 'physical', 'Next Move Games', 'active', 'source_bound',
     ARRAY['publisher:nextmove:hey-thats-my-fish:product-en','publisher:nextmove:hey-thats-my-fish:rulebook-2023-en']::text[])
  RETURNING id INTO v_ruleset_id;

  INSERT INTO public.rule_nodes
    (rule_set_id, rule_id, node_type, normalized_statement, sequence, verification_status,
     source_claim_ref, evidence_ref, source_url, source_locator, metadata)
  VALUES
    (v_ruleset_id,'setup-board','setup',
     '4枚のオーシャンボードを魚の向きが同じになるようにつなぎ、60枚の浮氷タイルを裏向きで混ぜてから、すべて表向きでランダムにボードへ置く。',
     10,'source_bound','hey-thats-my-fish:rule:setup-board','hey-thats-my-fish:binding:setup-board',
     'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf','hey-thats-my-fish:setup-board','{}'::jsonb),
    (v_ruleset_id,'setup-penguins','setup',
     '各プレイヤーは色を1色選ぶ。2人なら4個、3人なら3個、4人なら2個のペンギンを使い、最年少のプレイヤーから時計回りに、魚1匹の空いている浮氷タイルへ1個ずつ、全て置き終わるまで配置する。',
     20,'source_bound','hey-thats-my-fish:rule:setup-penguins','hey-thats-my-fish:binding:setup-penguins',
     'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf','hey-thats-my-fish:setup-penguins','{}'::jsonb),
    (v_ruleset_id,'turn-order','turn',
     'ゲームは最年少のプレイヤーから始め、以後は時計回りに手番を行う。各手番では、ペンギン1個を動かした後、そのペンギンが移動前にいた浮氷タイル1枚を取る。',
     30,'source_bound','hey-thats-my-fish:rule:turn-order','hey-thats-my-fish:binding:turn-order',
     'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf','hey-thats-my-fish:turn-order','{}'::jsonb),
    (v_ruleset_id,'move-penguin','action',
     '自分のペンギン1個を、六角形の6方向のうち1方向へ直線上に好きな距離だけ動かす。移動中に方向転換できず、他のペンギンがいる浮氷や浮氷のない場所へ移動したり、それらを通り抜けたりできない。',
     40,'source_bound','hey-thats-my-fish:rule:move-penguin','hey-thats-my-fish:binding:move-penguin',
     'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf','hey-thats-my-fish:move-penguin','{}'::jsonb),
    (v_ruleset_id,'collect-floe','effect',
     'ペンギンを動かしたら、そのペンギンが移動前にいた浮氷タイルを取り、自分の獲得タイルとして表向きで置く。',
     50,'source_bound','hey-thats-my-fish:rule:collect-floe','hey-thats-my-fish:binding:collect-floe',
     'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf','hey-thats-my-fish:collect-floe','{}'::jsonb),
    (v_ruleset_id,'unable-to-move','condition',
     '自分のどのペンギンも動かせなくなったプレイヤーは、その後の手番を行わない。自分のペンギンをすべてボードから取り除き、それらがいた浮氷タイルを自分の獲得タイルへ加える。',
     60,'source_bound','hey-thats-my-fish:rule:unable-to-move','hey-thats-my-fish:binding:unable-to-move',
     'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf','hey-thats-my-fish:unable-to-move','{}'::jsonb),
    (v_ruleset_id,'end-game','game_end',
     'すべてのペンギンがボードから取り除かれたらゲーム終了となる。獲得されずに残った浮氷タイルは箱へ戻す。',
     70,'source_bound','hey-thats-my-fish:rule:end-game','hey-thats-my-fish:binding:end-game',
     'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf','hey-thats-my-fish:end-game','{}'::jsonb),
    (v_ruleset_id,'victory','victory',
     '獲得した魚の合計が最も多いプレイヤーが勝つ。同点なら獲得した浮氷タイルが最も多いプレイヤーが勝ち、それも同数なら同点のプレイヤー全員が勝者となる。',
     80,'source_bound','hey-thats-my-fish:rule:victory','hey-thats-my-fish:binding:victory',
     'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/05/EN-HTMF-Rulebook-lowres.pdf','hey-thats-my-fish:victory','{}'::jsonb);

  INSERT INTO public.claims
    (claim_id, rule_set_id, claim_type, normalized_payload, target_type, rule_id,
     lifecycle_status, generator_provenance)
  SELECT 'hey-thats-my-fish:rule:' || rule_id, v_ruleset_id, 'normalized_rule_statement',
         jsonb_build_object('statement', normalized_statement), 'rule_node', rule_id, 'accepted',
         '{"method":"human_reviewed_official_rulebook","source":"Next Move Games official rulebook"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id = v_ruleset_id;

  INSERT INTO public.evidence_bindings
    (binding_id, claim_id, source_id, locator_id, relation,
     reviewer_provenance, generator_provenance, verified_at)
  SELECT 'hey-thats-my-fish:binding:' || rule_id,
         'hey-thats-my-fish:rule:' || rule_id,
         'publisher:nextmove:hey-thats-my-fish:rulebook-2023-en', source_locator, 'supports',
         '{"review":"human_reviewed","source":"official_rulebook"}'::jsonb,
         '{"migration":"108_review_hey_thats_my_fish_official_rules.sql"}'::jsonb, now()
  FROM public.rule_nodes WHERE rule_set_id = v_ruleset_id;

  SELECT count(*) INTO v_count FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id AND verification_status = 'source_bound';
  IF v_count <> 8 THEN RAISE EXCEPTION 'hey-thats-my-fish requires 8 RuleNodes, found %', v_count; END IF;

  SELECT count(*) INTO v_count FROM public.claims
  WHERE rule_set_id = v_ruleset_id AND lifecycle_status = 'accepted';
  IF v_count <> 8 THEN RAISE EXCEPTION 'hey-thats-my-fish requires 8 Claims, found %', v_count; END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id = 'publisher:nextmove:hey-thats-my-fish:rulebook-2023-en';
  IF v_count <> 8 THEN RAISE EXCEPTION 'hey-thats-my-fish requires 8 official EvidenceBindings, found %', v_count; END IF;

  UPDATE public.game_works
  SET canonical_title = 'Hey, That''s My Fish!', identity_status = 'verified', updated_at = now()
  WHERE id = v_work_id;

  UPDATE public.games
  SET title = 'Hey, That''s My Fish!',
      title_en = 'Hey, That''s My Fish!',
      title_ja = 'それはオレの魚だ！',
      identity_status = 'verified',
      identity_source = 'https://www.nextmove-games.com/en/hey-thats-my-fish/',
      source_url = 'https://www.nextmove-games.com/en/hey-thats-my-fish/',
      official_url = 'https://www.nextmove-games.com/en/hey-thats-my-fish/',
      source_trust = 'official_publisher',
      content_review_status = 'human_reviewed',
      publisher = 'Next Move Games',
      language_code = 'ja',
      source_revision = 'Next Move Games official product + © 2023 Plan B Games Inc. rulebook; reviewed 2026-08-29',
      min_players = 2, max_players = 4, play_time = 20,
      play_time_min_minutes = 20, play_time_max_minutes = 20, min_age = 8,
      amazon_url = 'https://www.amazon.co.jp/s?k=それはオレの魚だ&tag=bodogemikata-22',
      rules = '{}'::jsonb, rules_content = NULL,
      setup_summary = NULL, gameplay_summary = NULL, end_game_summary = NULL,
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.game_title_aliases
  SET title = 'それはオレの魚だ！', normalized_title = 'それはオレの魚だ', language_code = 'ja',
      source = 'https://arclightgames.jp/product/659hau/'
  WHERE game_id = v_game_id AND title = 'それは俺の魚だ！';

  IF NOT EXISTS (
    SELECT 1 FROM public.games
    WHERE id = v_game_id
      AND title = 'Hey, That''s My Fish!'
      AND title_ja = 'それはオレの魚だ！'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'human_reviewed'
      AND min_players = 2 AND max_players = 4
      AND play_time = 20 AND play_time_min_minutes = 20 AND play_time_max_minutes = 20
      AND min_age = 8 AND rules = '{}'::jsonb AND rules_content IS NULL
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'hey-thats-my-fish post-update verification failed';
  END IF;
END $$;

COMMIT;

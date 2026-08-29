BEGIN;

-- プレイヤー向け成功条件:
-- /games/high-society が Osprey Games 2018年版だけを根拠として、
-- 準備 → 通常の競り → 不名誉カードの競り → 終了 → 勝敗まで説明でき、検索公開されること。
-- 出典なしの旧 rules_content は公開ルールとして残さない。

INSERT INTO public.evidence_sources
  (source_id, url, document_identity, source_type, publisher_name, platform, language_code,
   revision_label, retrieved_at, trust_metadata)
VALUES
  ('publisher:osprey:high-society:rulebook-2018-en',
   'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf',
   'High Society Rulebook — Osprey Games edition © 2018 Osprey Publishing Ltd.',
   'publisher_rulebook', 'Osprey Games', 'physical', 'en', 'osprey-2018', now(),
   '{"trust":"official_publisher","use":"rules_and_edition_identity"}'::jsonb),
  ('publisher:osprey:high-society:catalog-2021-en',
   'https://www.ospreypublishing.com/media/dt5ejf0r/osg-jan-catalogue-2021-3-dec-digital_compressed-1.pdf',
   'Osprey Games January–June 2021 Catalogue — High Society listing',
   'publisher_catalog', 'Osprey Games', 'physical', 'en', '2021-catalogue', now(),
   '{"trust":"official_publisher","use":"player_count_age_play_time"}'::jsonb)
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
  ('high-society:setup','publisher:osprey:high-society:rulebook-2018-en',3,'Setup','Rulebook page 3'),
  ('high-society:auction-start','publisher:osprey:high-society:rulebook-2018-en',4,'Auction Rounds','Rulebook page 4'),
  ('high-society:bidding','publisher:osprey:high-society:rulebook-2018-en',4,'Bidding','Rulebook page 4'),
  ('high-society:passing','publisher:osprey:high-society:rulebook-2018-en',4,'Passing','Rulebook page 4'),
  ('high-society:normal-auction','publisher:osprey:high-society:rulebook-2018-en',4,'Auction Rounds','Last remaining player and new round'),
  ('high-society:disgrace-auction','publisher:osprey:high-society:rulebook-2018-en',5,'Disgrace!','Rulebook page 5'),
  ('high-society:disgrace-effects','publisher:osprey:high-society:rulebook-2018-en',5,'Disgrace!','Faux Pas, Passé, Scandale'),
  ('high-society:game-end','publisher:osprey:high-society:rulebook-2018-en',6,'Game End','Rulebook page 6'),
  ('high-society:cast-out','publisher:osprey:high-society:rulebook-2018-en',6,'Cast Out!','Rulebook page 6'),
  ('high-society:scoring','publisher:osprey:high-society:rulebook-2018-en',6,'Scoring','Scoring, prestige multipliers and tie breakers'),
  ('high-society:metadata','publisher:osprey:high-society:catalog-2021-en',14,'High Society','3–5 players · 10+ · 20min')
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
  FROM public.games WHERE slug = 'high-society' LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'High Society canonical game row is not part of the fixture; skipping migration';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical high-society game row is required';
  END IF;

  SELECT count(*) INTO v_count FROM public.rule_sets WHERE game_id = v_game_id;
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'high-society expected 0 existing RuleSets before migration, found %', v_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.games
    WHERE id = v_game_id
      AND identity_status = 'unverified'
      AND content_review_status IN ('unknown','review_required')
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'high-society pre-migration state changed; re-audit before publishing';
  END IF;

  INSERT INTO public.rule_sets
    (game_id, work_id, version, schema_version, language_code, edition_label, source_revision, is_active,
     revision_label, platform, publisher_name, status, verification_status, source_ids)
  VALUES
    (v_game_id, v_work_id, 1, '1.0', 'ja', 'High Society（Osprey Games 2018年版）',
     'Osprey Games official rulebook, this edition © 2018 Osprey Publishing Ltd.',
     true, 'osprey-2018', 'physical', 'Osprey Games', 'active', 'source_bound',
     ARRAY['publisher:osprey:high-society:rulebook-2018-en','publisher:osprey:high-society:catalog-2021-en']::text[])
  RETURNING id INTO v_ruleset_id;

  INSERT INTO public.rule_nodes
    (rule_set_id, rule_id, node_type, normalized_statement, sequence, verification_status,
     source_claim_ref, evidence_ref, source_url, source_locator, metadata)
  VALUES
    (v_ruleset_id,'setup','setup',
     '各プレイヤーは同じ色の11枚のお金カードを手札として受け取り、他のプレイヤーに見せない。16枚のステータスカードを混ぜて中央に裏向きの山札として置き、山札を混ぜたプレイヤーが最初のプレイヤーになる。',
     10,'source_bound','high-society:rule:setup','high-society:binding:setup',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:setup','{}'::jsonb),
    (v_ruleset_id,'auction-start','phase',
     '各ラウンドの開始時にステータスカードの山札の一番上を1枚表向きにする。通常はこのカードを最高額の入札者が獲得し、最初のプレイヤーから入札かパスを選ぶ。',
     20,'source_bound','high-society:rule:auction-start','high-society:binding:auction-start',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:auction-start','{}'::jsonb),
    (v_ruleset_id,'bidding','action',
     '入札する場合は手札から1枚以上のお金カードを自分の前に表向きで出し、場に出した自分のお金カードの合計額を宣言する。同じラウンドで再入札するときは新しいカードを追加するだけで、すでに出したカードは戻せない。新しい合計額は直前の入札額より高くなければならない。',
     30,'source_bound','high-society:rule:bidding','high-society:binding:bidding',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:bidding','{}'::jsonb),
    (v_ruleset_id,'passing','action',
     'パスする場合、そのラウンドですでに入札していれば自分が表向きで出したお金カードをすべて手札へ戻す。パスした後はそのラウンドでは再び入札できない。手番は左隣のプレイヤーへ移る。',
     40,'source_bound','high-society:rule:passing','high-society:binding:passing',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:passing','{}'::jsonb),
    (v_ruleset_id,'normal-auction','round_end',
     '不名誉カード以外の競りでは、他の全員がパスして最後に残ったプレイヤーがステータスカードを獲得する。落札者が場に出したお金カードは裏向きで捨て、落札者が次のラウンドの最初のプレイヤーになる。全員が入札せずにパスした場合も、最後に残ったプレイヤーが無料でカードを獲得する。',
     50,'source_bound','high-society:rule:normal-auction','high-society:binding:normal-auction',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:normal-auction','{}'::jsonb),
    (v_ruleset_id,'disgrace-auction','exception',
     '表になったカードが不名誉カードの場合は、そのカードを避けるために入札する。誰か1人がパスした時点でラウンドが終わり、パスしたプレイヤーが不名誉カードを受け取って自分が出していたお金カードを手札へ戻す。他の全員は場に出していたお金カードを裏向きで捨て、パスしたプレイヤーが次のラウンドを始める。',
     60,'source_bound','high-society:rule:disgrace-auction','high-society:binding:disgrace-auction',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:disgrace-auction','{}'::jsonb),
    (v_ruleset_id,'disgrace-effects','effect',
     'Faux Pasを受け取ったら自分の贅沢品カード1枚を選んで捨て、贅沢品カードがなければ次に受け取る贅沢品カードを捨てる。その後Faux Pasも捨てる。Passéはステータスを5減らし、Scandaleはゲーム終了時にステータスを半分にする。',
     70,'source_bound','high-society:rule:disgrace-effects','high-society:binding:disgrace-effects',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:disgrace-effects','{}'::jsonb),
    (v_ruleset_id,'game-end','game_end',
     'ステータスカードのうち濃い緑色の背景を持つ4枚は、3枚の名声カードとScandaleである。その4枚目が山札から表になった瞬間にゲームは終了し、そのカードの競りは行わない。',
     80,'source_bound','high-society:rule:game-end','high-society:binding:game-end',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:game-end','{}'::jsonb),
    (v_ruleset_id,'cast-out','condition',
     'ゲーム終了時に全員がお金カードの手札を公開して残金の合計を比べる。残金が最も少ないプレイヤーは全員勝者候補から除外される。',
     90,'source_bound','high-society:rule:cast-out','high-society:binding:cast-out',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:cast-out','{}'::jsonb),
    (v_ruleset_id,'scoring','victory',
     '贅沢品カードは記載値をステータスに加え、名声カード1枚につきステータスを2倍にし、不名誉カードの効果を適用する。除外されていない中でステータスが最も高いプレイヤーが勝つ。同点なら残金が多い方、それも同じなら最も価値の高い贅沢品カードを持つ方が勝つ。',
     100,'source_bound','high-society:rule:scoring','high-society:binding:scoring',
     'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf','high-society:scoring','{}'::jsonb);

  INSERT INTO public.claims
    (claim_id, rule_set_id, claim_type, normalized_payload, target_type, rule_id,
     lifecycle_status, generator_provenance)
  SELECT 'high-society:rule:' || rule_id, v_ruleset_id, 'normalized_rule_statement',
         jsonb_build_object('statement', normalized_statement), 'rule_node', rule_id, 'accepted',
         '{"method":"human_reviewed_official_rulebook","source":"Osprey Games official rulebook"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id = v_ruleset_id;

  INSERT INTO public.evidence_bindings
    (binding_id, claim_id, source_id, locator_id, relation,
     reviewer_provenance, generator_provenance, verified_at)
  SELECT 'high-society:binding:' || rule_id,
         'high-society:rule:' || rule_id,
         'publisher:osprey:high-society:rulebook-2018-en', source_locator, 'supports',
         '{"review":"human_reviewed","source":"official_rulebook"}'::jsonb,
         '{"migration":"112_review_high_society_osprey_2018.sql"}'::jsonb, now()
  FROM public.rule_nodes WHERE rule_set_id = v_ruleset_id;

  UPDATE public.game_works
  SET canonical_title = 'High Society', identity_status = 'verified', updated_at = now()
  WHERE id = v_work_id;

  UPDATE public.games
  SET title = 'High Society',
      title_en = 'High Society',
      min_players = 3,
      max_players = 5,
      play_time = 20,
      play_time_min_minutes = 20,
      play_time_max_minutes = 20,
      min_age = 10,
      published_year = 2018,
      edition_label = 'High Society（Osprey Games 2018年版）',
      language_code = 'en',
      publisher = 'Osprey Games',
      source_url = 'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf',
      official_url = 'https://www.ospreypublishing.com/ca/discover/gaming-resources/board-card-games/',
      identity_source = 'https://www.ospreypublishing.com/media/1fohbutt/hisoc_rulebook_for_web.pdf',
      source_revision = 'Osprey Games official rulebook; this edition © 2018 Osprey Publishing Ltd.; official catalogue metadata 3–5 players, 10+, 20min',
      identity_status = 'verified',
      source_trust = 'official_publisher',
      content_review_status = 'human_reviewed',
      rules_content = NULL,
      setup_summary = '各プレイヤーは同色の11枚のお金カードを秘密の手札として受け取り、16枚のステータスカードを混ぜて中央に裏向きで置く。',
      gameplay_summary = '各ラウンドでステータスカード1枚を公開し、お金カードで競る。通常カードは最後まで残ったプレイヤーが取り、不名誉カードは最初にパスしたプレイヤーが取る。',
      end_game_summary = '濃い緑色の背景を持つ4枚目のカードが公開されたら即終了する。残金が最少のプレイヤーを除外し、残った中でステータスが最も高いプレイヤーが勝つ。',
      summary = 'お金カードを使ってステータスカードを競り、終了時に残金が最少のプレイヤーを除外した後、最も高いステータスを得たプレイヤーが勝つ競りゲーム。',
      description = '各ラウンドで公開されたステータスカードをお金カードで競る。不名誉カードでは競りの目的が逆になり、最初にパスしたプレイヤーがそのカードを受け取る。終了時は残金が最少のプレイヤーを除外してからステータスを比較する。',
      updated_at = now()
  WHERE id = v_game_id;

  SELECT count(*) INTO v_count FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id AND verification_status = 'source_bound';
  IF v_count <> 10 THEN RAISE EXCEPTION 'high-society requires 10 source-bound RuleNodes, found %', v_count; END IF;

  SELECT count(*) INTO v_count FROM public.claims
  WHERE rule_set_id = v_ruleset_id AND lifecycle_status = 'accepted';
  IF v_count <> 10 THEN RAISE EXCEPTION 'high-society requires 10 accepted Claims, found %', v_count; END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id = 'publisher:osprey:high-society:rulebook-2018-en';
  IF v_count <> 10 THEN RAISE EXCEPTION 'high-society requires 10 official supporting EvidenceBindings, found %', v_count; END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.games
    WHERE id = v_game_id
      AND identity_status = 'verified'
      AND content_review_status = 'human_reviewed'
      AND source_trust = 'official_publisher'
      AND min_players = 3 AND max_players = 5
      AND play_time_min_minutes = 20 AND play_time_max_minutes = 20
      AND min_age = 10 AND published_year = 2018
      AND rules_content IS NULL
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'high-society reviewed production contract is not satisfied';
  END IF;
END $$;

COMMIT;

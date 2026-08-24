BEGIN;

-- Canonical scope: TendaysGames Japanese base edition of Ark Nova.
-- Rules authority: Feuerland Spiele Ark Nova official English rulebook Version 1.2.
-- Marine Worlds, Map Packs, Sanctuary, BGA alternatives, promos, and later variants are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:tendays:ark-nova-ja','https://tendaysgames.shop/?pid=166436141','アーク・ノヴァ 新たなる方舟 日本語版 — TendaysGames','publisher_product_page','TendaysGames','physical','ja','japanese-base-edition','{"authority":"publisher_localization","audit_date":"2026-08-24","scope":"japanese_base_edition_identity"}'::jsonb),
('publisher:feuerland:ark-nova-rules-v1.2','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','Ark Nova — official rulebook Version 1.2','publisher_rulebook','Feuerland Spiele','physical','en','v1.2','{"authority":"publisher","audit_date":"2026-08-24","scope":"ark_nova_base_game"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('ark-nova:rules:setup','publisher:feuerland:ark-nova-rules-v1.2',4,'Setup','Map A for first game; five action cards; 25 money; draw 8 Zoo cards and keep 4; draw 2 Final Scoring cards'),
('ark-nova:rules:turn','publisher:feuerland:ark-nova-rules-v1.2',8,'A Turn / The 5 Action Cards','choose one action card; slot 1-5 determines strength; after use move chosen card to slot 1 and shift intervening cards right'),
('ark-nova:rules:cards','publisher:feuerland:ark-nova-rules-v1.2',9,'Cards Action','gain Zoo cards from deck or display; action strength controls draw/snap options'),
('ark-nova:rules:build','publisher:feuerland:ark-nova-rules-v1.2',10,'Build Action','build standard/special enclosures, kiosks and pavilions according to action strength and placement rules'),
('ark-nova:rules:animals','publisher:feuerland:ark-nova-rules-v1.2',11,'Animals Action','play animals into empty enclosures after meeting requirements and paying cost'),
('ark-nova:rules:association','publisher:feuerland:ark-nova-rules-v1.2',14,'Association Action','use association workers for reputation, partner zoos, universities, conservation projects, and donations'),
('ark-nova:rules:sponsors','publisher:feuerland:ark-nova-rules-v1.2',17,'Sponsors Action','play Sponsor cards or advance the Break token for money'),
('ark-nova:rules:x-token','publisher:feuerland:ark-nova-rules-v1.2',18,'X-Token Action','instead of one of the five actions, select and move an action card to slot 1 and gain exactly one X-token'),
('ark-nova:rules:break','publisher:feuerland:ark-nova-rules-v1.2',18,'Break','when Break token reaches final space finish current turn, then hand-limit cleanup, token cleanup, worker return, display refresh, income, and reset break track'),
('ark-nova:rules:end','publisher:feuerland:ark-nova-rules-v1.2',19,'End of Game & Final Scoring','game end triggers when Appeal and Conservation counters are in the same scoring area or have passed one another'),
('ark-nova:rules:scoring','publisher:feuerland:ark-nova-rules-v1.2',19,'Determine Victory Points','apply final scoring effects then subtract target appeal number from appeal value; highest positive Victory Point total wins'),
('ark-nova:rules:tiebreak','publisher:feuerland:ark-nova-rules-v1.2',19,'Determine Victory Points','tied player who supported most Conservation Projects wins; if still tied share victory')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid; v_count integer;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='ark-nova' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Ark Nova canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Ark Nova Work row is required'; END IF;

  UPDATE public.games SET
    title='Ark Nova',title_ja='アーク・ノヴァ',title_en='Ark Nova',
    description='現代的で科学的に運営される動物園を設計し、囲いを建設して動物を迎え、保全プロジェクトを支援する戦略ゲーム。',
    summary='手番では5枚のアクションカードから1枚を選び、カード位置に応じた強さで実行する。魅力と保全の2トラックを進め、両カウンターが同じ得点エリアに入るか交差すると終了が近づく。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://tendaysgames.shop/?pid=166436141',
    source_url='https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf',
    official_url='https://tendaysgames.shop/?pid=166436141',source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='アーク・ノヴァ 新たなる方舟 日本語版',language_code='ja',publisher='Feuerland Spiele / TendaysGames',
    source_revision='TendaysGames Japanese base edition; Feuerland Spiele Ark Nova official rulebook Version 1.2; audited 2026-08-24',
    min_players=1,max_players=4,play_time=150,min_age=14,published_year=2021,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='アーク・ノヴァ 新たなる方舟 日本語版'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='feuerland-rulebook-v1.2'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','アーク・ノヴァ 新たなる方舟 日本語版',
      'TendaysGames Japanese base edition; Feuerland Spiele Ark Nova official rulebook Version 1.2; audited 2026-08-24',
      true,'feuerland-rulebook-v1.2','physical','Feuerland Spiele / TendaysGames','active','source_bound',
      ARRAY['publisher:tendays:ark-nova-ja','publisher:feuerland:ark-nova-rules-v1.2']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',
      source_revision='TendaysGames Japanese base edition; Feuerland Spiele Ark Nova official rulebook Version 1.2; audited 2026-08-24',
      is_active=true,publisher_name='Feuerland Spiele / TendaysGames',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:tendays:ark-nova-ja','publisher:feuerland:ark-nova-rules-v1.2']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.base','setup','初回プレイでは各自Map Aを使う。各プレイヤーは5種類のアクションカードをside Iで配置し、25金を受け取る。Zooカードを8枚引いて4枚を手札に残し、最終得点カードを2枚受け取る。',10,'source_bound','ark-nova:rule:setup.base','ark-nova:binding:setup.base','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:setup','{}'::jsonb),
  (v_ruleset_id,'turn.action-card','turn','手番では5枚のアクションカードから1枚を選ぶ。カードがあるスロット1〜5がアクション強度となり、実行後は選んだカードをスロット1へ移し、その左側にあったカードを右へ1つずつずらす。',20,'source_bound','ark-nova:rule:turn.action-card','ark-nova:binding:turn.action-card','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:turn','{}'::jsonb),
  (v_ruleset_id,'action.cards','action','「カード」アクションでは山札または公開カード列からZooカードを獲得する。引ける枚数や公開列から直接取れる条件はアクション強度とカードの改良状態に従う。',30,'source_bound','ark-nova:rule:action.cards','ark-nova:binding:action.cards','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:cards','{}'::jsonb),
  (v_ruleset_id,'action.build','action','「建設」アクションでは動物用の標準・特殊な囲い、キオスク、パビリオンなどを動物園マップへ建設する。建設可能な内容はアクション強度と配置条件に従う。',40,'source_bound','ark-nova:rule:action.build','ark-nova:binding:action.build','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:build','{}'::jsonb),
  (v_ruleset_id,'action.animals','action','「動物」アクションでは、必要条件を満たしてコストを支払い、空いている適切な囲いへ動物カードをプレイする。動物は魅力や能力、保全に必要なアイコンをもたらす。',50,'source_bound','ark-nova:rule:action.animals','ark-nova:binding:action.animals','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:animals','{}'::jsonb),
  (v_ruleset_id,'action.association','action','「協会」アクションでは協会職員を使い、評判を上げる、提携動物園や大学を得る、保全プロジェクトを支援する、寄付するなどの協会活動を行う。',60,'source_bound','ark-nova:rule:action.association','ark-nova:binding:action.association','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:association','{}'::jsonb),
  (v_ruleset_id,'action.sponsors','action','「スポンサー」アクションではスポンサー・カードをプレイするか、ブレークトークンを進めて金を得る。改良後は条件の範囲で複数のスポンサー・カードを続けてプレイできる。',70,'source_bound','ark-nova:rule:action.sponsors','ark-nova:binding:action.sponsors','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:sponsors','{}'::jsonb),
  (v_ruleset_id,'action.x-token','action','5種類の通常アクションを実行できない、または実行したくない場合、任意のアクションカードを選んで通常どおりスロット1へ移し、代わりにXトークンを1個得る。',80,'source_bound','ark-nova:rule:action.x-token','ark-nova:binding:action.x-token','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:x-token','{}'::jsonb),
  (v_ruleset_id,'break.resolve','round_end','ブレークトークンが最後のマスに到達したら現在の手番を完了してブレークを行う。手札上限調整、アクションカード上の一時トークン返却、協会職員回収、公開列更新、収入獲得を処理し、ブレークトークンを人数対応の開始位置へ戻す。',90,'source_bound','ark-nova:rule:break.resolve','ark-nova:binding:break.resolve','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:break','{}'::jsonb),
  (v_ruleset_id,'game.end','game_end','手番終了時またはブレーク中に、自分の保全カウンターと魅力カウンターが同じ得点エリアに入るか互いを追い越したらゲーム終了をトリガーする。手番終了でトリガーした場合は他のプレイヤーが1手番ずつ、ブレーク中なら全員が1手番ずつ追加で行う。',100,'source_bound','ark-nova:rule:game.end','ark-nova:binding:game.end','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:end','{}'::jsonb),
  (v_ruleset_id,'game.scoring','scoring','最終得点効果を処理した後、保全カウンターがある得点エリアの最小魅力値を目標値とし、自分の魅力値からその目標値を引いた値を勝利点とする。最も高い勝利点のプレイヤーが勝つ。',110,'source_bound','ark-nova:rule:game.scoring','ark-nova:binding:game.scoring','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:scoring','{}'::jsonb),
  (v_ruleset_id,'game.tiebreak','victory','勝利点が同点なら、より多くの保全プロジェクトを支援した同点者が勝つ。それも同じなら同点者全員が勝利を分かち合う。',120,'source_bound','ark-nova:rule:game.tiebreak','ark-nova:binding:game.tiebreak','https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf','ark-nova:rules:tiebreak','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'ark-nova:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"ark_nova_base_game"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND rule_id IN (
    'setup.base','turn.action-card','action.cards','action.build','action.animals','action.association','action.sponsors','action.x-token','break.resolve','game.end','game.scoring','game.tiebreak'
  )
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'ark-nova:binding:'||rn.rule_id,'ark-nova:rule:'||rn.rule_id,'publisher:feuerland:ark-nova-rules-v1.2',rn.source_locator,'supports',
    '{"review":"first_party_rulebook","audit_date":"2026-08-24"}'::jsonb,
    '{"method":"publisher_rulebook_normalization"}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id AND rn.rule_id IN (
    'setup.base','turn.action-card','action.cards','action.build','action.animals','action.association','action.sponsors','action.x-token','break.resolve','game.end','game.scoring','game.tiebreak'
  )
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  SELECT count(*) INTO v_count FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound';
  IF v_count < 12 THEN RAISE EXCEPTION 'Ark Nova source-bound RuleNode count %, expected >= 12',v_count; END IF;
  SELECT count(*) INTO v_count FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted';
  IF v_count < 12 THEN RAISE EXCEPTION 'Ark Nova accepted Claim count %, expected >= 12',v_count; END IF;
  SELECT count(*) INTO v_count FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id
    WHERE c.rule_set_id=v_ruleset_id AND c.target_type='rule_node' AND c.lifecycle_status='accepted' AND eb.relation='supports';
  IF v_count < 12 THEN RAISE EXCEPTION 'Ark Nova supporting EvidenceBinding count %, expected >= 12',v_count; END IF;
END $$;

COMMIT;

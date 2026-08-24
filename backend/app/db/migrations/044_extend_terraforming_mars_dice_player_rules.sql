BEGIN;

-- Extend the existing Arclight Japanese revised RuleSet with player-facing
-- source-bound rules from the 2024-05-30 canonical revision.
-- The Corporate Era expansion and promo-card rules remain outside this base projection.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES (
  'publisher:arclight:tm-dice:revised-2024-05-30',
  'https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf',
  'Terraforming Mars: The Dice Game Japanese revised rulebook',
  'publisher_rulebook',
  'Arclight Games',
  'physical',
  'ja',
  '2024-05-30',
  '{"authority":"publisher","role":"canonical_for_arclight_japanese_revised_rules","audit_date":"2026-08-24"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,
  document_identity=EXCLUDED.document_identity,
  source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,
  platform=EXCLUDED.platform,
  language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,
  trust_metadata=EXCLUDED.trust_metadata,
  updated_at=now();

INSERT INTO public.source_locators (
  locator_id, source_id, page_number, section_heading, external_reference
) VALUES
  ('tm-dice:rulebook:setup','publisher:arclight:tm-dice:revised-2024-05-30',3,'ゲームの準備','Base-game multiplayer setup: board, oceans, parameters, decks, awards, milestones, corporations, starting resources, and first-player handicap.'),
  ('tm-dice:rulebook:turn','publisher:arclight:tm-dice:revised-2024-05-30',4,'ゲームの遊び方','On each turn choose either a Production Turn or an Action Turn.'),
  ('tm-dice:rulebook:production','publisher:arclight:tm-dice:revised-2024-05-30',4,'産出ターン','Keep up to three resource dice, refill hand to five, roll production dice, and refresh used blue cards.'),
  ('tm-dice:rulebook:action','publisher:arclight:tm-dice:revised-2024-05-30',4,'アクションターン','An Action Turn consists of one support action followed by one main action.'),
  ('tm-dice:rulebook:card-play','publisher:arclight:tm-dice:revised-2024-05-30',5,'カードのプレイ','Playing a project card is a main action; pay its resource cost and resolve its effects.'),
  ('tm-dice:rulebook:terraform','publisher:arclight:tm-dice:revised-2024-05-30',6,'ゲームの特徴／アイコン解説','Terraforming advances ocean, temperature, or oxygen and normally awards 2 VP.'),
  ('tm-dice:rulebook:global-end','publisher:arclight:tm-dice:revised-2024-05-30',6,'ゲームの特徴／アイコン解説','When two of the three global parameters are completed, each player gets one final turn.'),
  ('tm-dice:rulebook:final-scoring','publisher:arclight:tm-dice:revised-2024-05-30',9,'ゲームの終了','Final scoring includes awards, milestones, and card VP; highest VP wins, with production-dice capacity as tiebreak.'),
  ('tm-dice:rulebook:solo','publisher:arclight:tm-dice:revised-2024-05-30',10,'1人ゲームのルール','Solo play uses 50 turns and requires all three global parameters; failure skips final scoring.')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,
  page_number=EXCLUDED.page_number,
  section_heading=EXCLUDED.section_heading,
  external_reference=EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_work_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT g.id, g.work_id INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug='terraforming-mars-the-dice-game'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Terraforming Mars: The Dice Game row not present in this fixture; skipping catalog-bound extension';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Terraforming Mars: The Dice Game Work row is required';
  END IF;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id=v_game_id
    AND COALESCE(rs.language_code,'')='ja'
    AND COALESCE(rs.edition_label,'')='アークライト日本語版 改訂版 第2刷'
    AND COALESCE(rs.platform,'')='physical'
    AND COALESCE(rs.revision_label,'')='2024-05-30'
    AND COALESCE(rs.variant_label,'')=''
    AND rs.version=1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Migration 024 source-bound Terraforming Mars Dice RuleSet is required';
  END IF;

  UPDATE public.games SET
    title='Terraforming Mars: The Dice Game',
    title_ja='テラフォーミング・マーズ ダイスゲーム',
    title_en='Terraforming Mars: The Dice Game',
    description='専用ダイスで資源を生み出し、カードとアクションで火星の海洋・気温・酸素濃度を発展させるダイスゲーム。',
    summary='各手番は産出ターンかアクションターンを選ぶ。3つのグローバル・パラメータのうち2つが完成すると全員が最後の1手番を行い、最終的な勝利点を競う。',
    rules='{}'::jsonb,
    rules_content=NULL,
    structured_data='{}'::jsonb,
    setup_summary=NULL,
    gameplay_summary=NULL,
    end_game_summary=NULL,
    identity_status='verified',
    identity_source='https://arclightgames.jp/product/826ter/',
    source_url='https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf',
    official_url='https://arclightgames.jp/product/826ter/',
    source_trust='official_publisher',
    content_review_status='review_required',
    is_official=true,
    edition_label='アークライト日本語版 改訂版 第2刷',
    language_code='ja',
    publisher='FryxGames / Arclight Games',
    source_revision='Arclight Japanese revised rulebook, 2024-04-30 publication with 2024-05-30 time-marker correction',
    min_players=1,
    max_players=4,
    play_time=45,
    min_age=14,
    published_year=2023,
    updated_at=now()
  WHERE id=v_game_id;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
    (v_ruleset_id,'setup.base','setup','火星ボードを中央に置き、海洋タイル7枚を海洋アイコン上に重ねる。酸素濃度を0%、気温を-32°Cに設定する。各プレイヤーは色を選び、VPを0に置く。プロジェクトとボーナスを準備し、褒賞3個と称号3枚をランダムに用意する。各プレイヤーはプロジェクト5枚と企業2枚を受け取り、企業1枚を選んで公開し、開始時ボーナスと開始資源を受け取る。親は1人ゲームを除き、自分の資源1個を最後手番のプレイヤーへ渡す。',10,'source_bound','tm-dice:rule:setup.base','tm-dice:binding:setup.base','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:setup','{}'::jsonb),
    (v_ruleset_id,'turn.choice','turn','各手番では「産出ターン」か「アクションターン」のどちらか1つを選んで行う。手番は親から時計回りに進む。',20,'source_bound','tm-dice:rule:turn.choice','tm-dice:binding:turn.choice','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:turn','{}'::jsonb),
    (v_ruleset_id,'turn.production','turn','産出ターンでは、手元の資源ダイスを最大3個まで維持して残りを戻し、任意枚数の手札を捨て、手札が5枚になるまで補充する。その後、企業カードと緑色カードの産出欄に示されたダイスを獲得して振り、使用済みの青色カードを未使用に戻す。',30,'source_bound','tm-dice:rule:turn.production','tm-dice:binding:turn.production','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:production','{}'::jsonb),
    (v_ruleset_id,'turn.action','action','アクションターンは、補助アクション1回を行った後、メインアクション1回を行う。メインアクションとしてカードのプレイ、2回目の補助アクション、各種テラフォーミング、都市配置、3メガクレジット資源による2VP獲得、青色カードのメインアクションなどを選べる。',40,'source_bound','tm-dice:rule:turn.action','tm-dice:binding:turn.action','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:action','{}'::jsonb),
    (v_ruleset_id,'card.play','action','プロジェクト・カードをプレイするには、カード左上のコストに対応する資源を支払う。ワイルド・トークンは任意の資源1個として使える。コスト支払い後、カード効果を任意の順番で適用し、実行できない部分は無視する。',50,'source_bound','tm-dice:rule:card.play','tm-dice:binding:card.play','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:card-play','{}'::jsonb),
    (v_ruleset_id,'terraform.advance','action','海洋タイルの配置、気温の1段階上昇、酸素濃度の1段階上昇を行うたび、通常は2VPを獲得する。完成済みのグローバル・パラメータに対して同じアクションを行うこともでき、その場合はパラメータを進めず1VPを獲得する。',60,'source_bound','tm-dice:rule:terraform.advance','tm-dice:binding:terraform.advance','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:terraform','{}'::jsonb),
    (v_ruleset_id,'game.end.multiplayer','game_end','海洋・気温・酸素濃度の3つのグローバル・パラメータのうち2つが完成した時点で終了が決定する。その後、2つ目を完成させたプレイヤーを含む全プレイヤーが最後の手番を1回ずつ行ってからゲームを終了する。',70,'source_bound','tm-dice:rule:game.end.multiplayer','tm-dice:binding:game.end.multiplayer','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:global-end','{}'::jsonb),
    (v_ruleset_id,'game.scoring','scoring','ゲーム終了時は褒賞、獲得した称号、プレイしたカードに記された最終得点用VPを加算し、最もVPが多いプレイヤーが勝つ。同点なら各カードの産出欄にある資源ダイスの合計数が多いプレイヤーが勝ち、それも同数なら勝者は決まらない。',80,'source_bound','tm-dice:rule:game.scoring','tm-dice:binding:game.scoring','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:final-scoring','{}'::jsonb),
    (v_ruleset_id,'solo.end','game_end','1人ゲームでは50手番以内に海洋・気温・酸素濃度の3つすべてを完成させる。達成できれば最終得点計算へ進み、50手番で達成できなければ失敗として最終得点計算を行わない。時間マーカーは最初の手番前に1マス進め、その後は各手番終了時に進める。',90,'source_bound','tm-dice:rule:solo.end','tm-dice:binding:solo.end','https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf','tm-dice:rulebook:solo','{"player_count":1}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,
    normalized_statement=EXCLUDED.normalized_statement,
    sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,
    source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,
    source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,
    updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT
    'tm-dice:rule:'||rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement',rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"arclight_japanese_revised_base_game"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id=v_ruleset_id
    AND rn.rule_id IN ('setup.base','turn.choice','turn.production','turn.action','card.play','terraform.advance','game.end.multiplayer','game.scoring','solo.end')
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,
    claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,
    rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,
    updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
    ('tm-dice:binding:setup.base','tm-dice:rule:setup.base','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:setup','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now()),
    ('tm-dice:binding:turn.choice','tm-dice:rule:turn.choice','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:turn','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now()),
    ('tm-dice:binding:turn.production','tm-dice:rule:turn.production','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:production','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now()),
    ('tm-dice:binding:turn.action','tm-dice:rule:turn.action','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:action','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now()),
    ('tm-dice:binding:card.play','tm-dice:rule:card.play','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:card-play','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now()),
    ('tm-dice:binding:terraform.advance','tm-dice:rule:terraform.advance','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:terraform','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now()),
    ('tm-dice:binding:game.end.multiplayer','tm-dice:rule:game.end.multiplayer','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:global-end','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now()),
    ('tm-dice:binding:game.scoring','tm-dice:rule:game.scoring','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:final-scoring','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now()),
    ('tm-dice:binding:solo.end','tm-dice:rule:solo.end','publisher:arclight:tm-dice:revised-2024-05-30','tm-dice:rulebook:solo','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,
    source_id=EXCLUDED.source_id,
    locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,
    reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,
    verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') < 9 THEN
    RAISE EXCEPTION 'Terraforming Mars Dice requires at least 9 source-bound player-facing RuleNodes';
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.rule_nodes rn
    WHERE rn.rule_set_id=v_ruleset_id AND rn.verification_status='source_bound'
      AND NOT EXISTS (
        SELECT 1 FROM public.claims c
        JOIN public.evidence_bindings eb ON eb.claim_id=c.claim_id AND eb.relation='supports'
        WHERE c.rule_set_id=v_ruleset_id AND c.rule_id=rn.rule_id AND c.lifecycle_status='accepted'
      )
  ) THEN
    RAISE EXCEPTION 'Every Terraforming Mars Dice source-bound RuleNode requires accepted supporting evidence';
  END IF;
END $$;

COMMIT;

BEGIN;

-- Canonical scope: AMIGO Elfenland base game, rules Version 3.0 (2013).
-- The optional destination-card variation and Favor of the Towns expansion are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:amigo:elfenland:product','https://www.amigo-spiele.de/elfenland_2610_1110','Elfenland','publisher_product_page','AMIGO Spiel + Freizeit','physical','de','current-product-page','{"authority":"publisher","audit_date":"2026-08-24","scope":"product_identity_and_components"}'::jsonb),
('publisher:amigo:elfenland:rules-ja-v3','https://blog.amigo-spiele.de/content/ap/rule/02610-JP-AmigoRule.pdf','Elfenland ルール Version 3.0','publisher_rulebook','AMIGO Spiel + Freizeit','physical','ja','3.0-2013','{"authority":"publisher","audit_date":"2026-08-24","scope":"official_japanese_rulebook"}'::jsonb),
('publisher:amigo:elfenland:rules-en-v3','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','Elfenland Rules Version 3.0','publisher_rulebook','AMIGO Spiel + Freizeit','physical','en','3.0-2013','{"authority":"publisher","audit_date":"2026-08-24","scope":"base_game_rule_authority"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('elfenland:product:overview','publisher:amigo:elfenland:product','Elfenland','20 towns; four rounds; 120 town pieces; 72 travel cards; 48 transportation counters'),
('elfenland:rules:setup','publisher:amigo:elfenland:rules-en-v3','How To Set Up The Game','Elf Boots/Town Pieces; Town Cards excluded from base game; travel cards; round cards; transportation counters; obstacles'),
('elfenland:rules:round','publisher:amigo:elfenland:rules-en-v3','How To Play The Game','six phases per round'),
('elfenland:rules:travel-cards','publisher:amigo:elfenland:rules-en-v3','1. Deal Travel Cards','eight cards in first round; replenish to eight in later rounds'),
('elfenland:rules:counters','publisher:amigo:elfenland:rules-en-v3','2./3. Draw Transportation Counters','one hidden counter then additional counters; four in first round; one may be retained'),
('elfenland:rules:route','publisher:amigo:elfenland:rules-en-v3','4. Plan Travel Routes','alternate legal transportation-counter placement; one counter per road'),
('elfenland:rules:obstacle','publisher:amigo:elfenland:rules-en-v3','Obstacles','one obstacle per player for the game; extra matching travel-card cost; no river/lake obstacle'),
('elfenland:rules:move','publisher:amigo:elfenland:rules-en-v3','5. Move The Elf Boots','matching travel cards; terrain costs; all players may use placed counters'),
('elfenland:rules:water','publisher:amigo:elfenland:rules-en-v3','Traveling On Rivers / Ferries','raft-card costs for rivers and lakes'),
('elfenland:rules:caravan','publisher:amigo:elfenland:rules-en-v3','The Caravan','three arbitrary travel cards on roads; four when an obstacle applies'),
('elfenland:rules:round-end','publisher:amigo:elfenland:rules-en-v3','6. Finish The Round','advance round card; pass starting player; retain at most one transportation counter; remove used obstacles'),
('elfenland:rules:end','publisher:amigo:elfenland:rules-en-v3','End Of Game','end after round four; most Town Pieces wins; travel-card tiebreak; early all-town win')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='elfenland' LIMIT 1;
  IF v_game_id IS NULL OR v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Elfenland Game/Work row is required'; END IF;

  UPDATE public.games SET
    title='Elfenland',title_ja='エルフェンランド',title_en='Elfenland',
    description='エルフの旅人として、地形ごとに使える移動手段と移動カードを組み合わせ、4ラウンドでできるだけ多くの街を訪れるルート計画ゲーム。',
    summary='移動手段タイルを街道へ配置し、対応する移動カードを支払って街を巡る。4ラウンド終了時に最も多くの訪問地コマを集めたプレイヤーが勝つ。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://www.amigo-spiele.de/elfenland_2610_1110',
    source_url='https://www.amigo-spiele.de/elfenland_2610_1110',official_url='https://www.amigo-spiele.de/elfenland_2610_1110',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='AMIGO Elfenland（Rules Version 3.0 / 2013）',language_code='ja',publisher='AMIGO Spiel + Freizeit',
    source_revision='AMIGO Elfenland Rules Version 3.0 (2013), official Japanese/English rulebooks; audited 2026-08-24',
    min_players=2,max_players=6,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id
    AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='AMIGO Elfenland（Rules Version 3.0 / 2013）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='amigo-v3.0-2013-ja'
    AND COALESCE(variant_label,'')=''
    AND version=1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','AMIGO Elfenland（Rules Version 3.0 / 2013）',
      'AMIGO Elfenland Rules Version 3.0 (2013), official Japanese/English rulebooks; audited 2026-08-24',
      true,'amigo-v3.0-2013-ja','physical','AMIGO Spiel + Freizeit','active','source_bound',
      ARRAY['publisher:amigo:elfenland:product','publisher:amigo:elfenland:rules-ja-v3','publisher:amigo:elfenland:rules-en-v3']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,schema_version='1.0',
      source_revision='AMIGO Elfenland Rules Version 3.0 (2013), official Japanese/English rulebooks; audited 2026-08-24',
      is_active=true,publisher_name='AMIGO Spiel + Freizeit',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:amigo:elfenland:product','publisher:amigo:elfenland:rules-ja-v3','publisher:amigo:elfenland:rules-en-v3']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.base','setup','各プレイヤーは同じ色のエルフの長靴コマ1個と訪問地コマ20個を受け取る。長靴コマをエルフェンホールドに置き、自分の訪問地コマを残り20の街に1個ずつ置く。目的地カード12枚は基本ゲームでは使わない。移動カード72枚を山札にし、ラウンドカードは1が一番上、4が一番下になるよう重ねる。移動手段タイル48枚を混ぜて5枚を常に公開し、各プレイヤーは一覧カード1枚と障害タイル1枚を受け取る。',10,'source_bound','elfenland:rule:setup.base','elfenland:binding:setup.base','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:setup','{}'::jsonb),
  (v_ruleset_id,'round.phases','turn','各ラウンドは、移動カードの配布、裏向き移動手段タイル1枚の獲得、追加の移動手段タイル獲得、ルート計画、長靴コマの移動、ラウンド終了処理の6段階で進む。',20,'source_bound','elfenland:rule:round.phases','elfenland:binding:round.phases','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:round','{}'::jsonb),
  (v_ruleset_id,'round.travel-cards','condition','第1ラウンドは各プレイヤーに移動カード8枚を配る。以後のラウンドでは移動カードを混ぜ直し、各プレイヤーの手札が8枚になるまで補充する。',30,'source_bound','elfenland:rule:round.travel-cards','elfenland:binding:round.travel-cards','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:travel-cards','{}'::jsonb),
  (v_ruleset_id,'round.transport-counters','condition','各ラウンドでまず各プレイヤーは裏向きの移動手段タイルを1枚取る。その後、公開または裏向きの山から追加タイルを取る。第1ラウンドは合計4枚になり、ラウンド終了時に残した1枚がある後続ラウンドでは最大5枚を持つことがある。',40,'source_bound','elfenland:rule:round.transport-counters','elfenland:binding:round.transport-counters','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:counters','{}'::jsonb),
  (v_ruleset_id,'route.plan','action','ルート計画では順番に移動手段タイルを街道へ1枚ずつ置く。1本の街道に置ける移動手段タイルは1枚で、その地形で利用可能な移動手段だけを置ける。配置されたタイルは置いた本人以外のプレイヤーも利用できる。',50,'source_bound','elfenland:rule:route.plan','elfenland:binding:route.plan','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:route','{}'::jsonb),
  (v_ruleset_id,'route.obstacle','condition','各プレイヤーはゲーム中に自分の障害タイルを1回だけ、すでに移動手段タイルが置かれた街道へ置ける。その街道を通るには通常必要な移動カードに加えて同じ種類のカード1枚が必要になる。川や湖には障害タイルを置けない。',60,'source_bound','elfenland:rule:route.obstacle','elfenland:binding:route.obstacle','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:obstacle','{}'::jsonb),
  (v_ruleset_id,'move.roads','action','移動では、街道上の移動手段タイルと同じ種類の移動カードを必要枚数出して隣の街へ進む。地形によって同じ移動手段でも必要枚数が異なり、条件を満たす限り1回の移動フェイズで複数の街道を続けて移動できる。同じ街道を往復して使う場合も、その都度カードを支払う。',70,'source_bound','elfenland:rule:move.roads','elfenland:binding:move.roads','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:move','{}'::jsonb),
  (v_ruleset_id,'move.water','condition','川は移動手段タイルを使わず、いかだカードで移動する。川下りは1枚、川上りは2枚を支払う。2つの湖を渡るフェリーは1回の移動につき、いかだカード2枚を支払う。',80,'source_bound','elfenland:rule:move.water','elfenland:binding:move.water','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:water','{}'::jsonb),
  (v_ruleset_id,'move.caravan','action','街道に移動手段タイルがあるが対応する移動カードを使えない場合、任意の移動カード3枚を出してキャラバンとしてその街道を移動できる。障害タイルがある街道では任意の4枚が必要になる。キャラバンは川や湖では使えない。',90,'source_bound','elfenland:rule:move.caravan','elfenland:binding:move.caravan','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:caravan','{}'::jsonb),
  (v_ruleset_id,'round.finish','condition','全員の移動後、ラウンドカードを進めてスタートプレイヤーカードを左隣へ渡す。各プレイヤーは手元の移動手段タイルを1枚だけ残し、それ以外と盤上の移動手段タイルを回収して混ぜる。使用済みの障害タイルはゲームから除外する。',100,'source_bound','elfenland:rule:round.finish','elfenland:binding:round.finish','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:round-end','{}'::jsonb),
  (v_ruleset_id,'game.end','condition','ゲームは第4ラウンド終了後に終わり、集めた自分の訪問地コマが最も多いプレイヤーが勝つ。同数なら手札に残った移動カードが多いプレイヤーが勝つ。第3ラウンド終了前までに20個すべての訪問地コマを集めたプレイヤーは直ちに勝利する。',110,'source_bound','elfenland:rule:game.end','elfenland:binding:game.end','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:end','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT
    'elfenland:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"elfenland_base_game_v3"}'::jsonb
  FROM public.rule_nodes
  WHERE rule_set_id=v_ruleset_id AND rule_id IN(
    'setup.base','round.phases','round.travel-cards','round.transport-counters','route.plan','route.obstacle',
    'move.roads','move.water','move.caravan','round.finish','game.end'
  )
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
  ('elfenland:binding:setup.base','elfenland:rule:setup.base','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:setup','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:round.phases','elfenland:rule:round.phases','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:round','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:round.travel-cards','elfenland:rule:round.travel-cards','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:travel-cards','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:round.transport-counters','elfenland:rule:round.transport-counters','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:counters','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:route.plan','elfenland:rule:route.plan','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:route','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:route.obstacle','elfenland:rule:route.obstacle','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:obstacle','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:move.roads','elfenland:rule:move.roads','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:move','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:move.water','elfenland:rule:move.water','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:water','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:move.caravan','elfenland:rule:move.caravan','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:caravan','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:round.finish','elfenland:rule:round.finish','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:round-end','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:game.end','elfenland:rule:game.end','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:end','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,
    reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;
END $$;

COMMIT;

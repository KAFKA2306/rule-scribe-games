BEGIN;

-- Canonical scope: Sugorokuya's June 2024 Japanese physical edition of Sky Team,
-- using Scorpion Masque's base Landing Procedure as rule authority.
-- Excludes Flight Log advanced scenarios/modules, Ready to Play add-on scenarios,
-- Board Game Arena behavior, and the Alarms and Turbulences expansion.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('localizer:sugorokuya:sky-team:product','https://sugorokuya.jp/p/sky-team','スカイチーム | すごろくやのボードゲーム','localized_product_page','すごろくや','physical','ja','jp-edition-2024-06','{"authority":"official_localizer_and_distributor","audit_date":"2026-08-24","scope":"japanese_product_identity"}'::jsonb),
('publisher:scorpion:sky-team:landing-procedure','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','Sky Team - Landing Procedure','publisher_rulebook','Le Scorpion Masqué','physical','en','landing-procedure-2023-06-06','{"authority":"publisher","audit_date":"2026-08-24","scope":"base_montreal_landing_procedure_only"}'::jsonb),
('publisher:scorpion:sky-team:product','https://www.scorpionmasque.com/en/sky-team','Sky Team official product page','publisher_product_page','Le Scorpion Masqué','physical','en','current-base-game','{"authority":"publisher","audit_date":"2026-08-24","scope":"base_game_identity"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('sky-team:sugorokuya:product','localizer:sugorokuya:sky-team:product','製品情報','国内版発行年 2024年6月、2人専用、20分、12歳以上、説明書言語 日本語、JAN 4571345801141'),
('sky-team:landing:setup','publisher:scorpion:sky-team:landing-procedure','BEFORE EACH GAME','p.3 basic-game setup; advanced-module components are explicitly excluded'),
('sky-team:landing:round','publisher:scorpion:sky-team:landing-procedure','GAME / STRATEGY DISCUSSION AND DICE ROLLS','p.4 seven rounds, three phases, communication boundary, hidden dice'),
('sky-team:landing:placement','publisher:scorpion:sky-team:landing-procedure','DICE PLACEMENT - GENERAL RULES','p.4 alternating one-die placement with colour/number constraints'),
('sky-team:landing:mandatory','publisher:scorpion:sky-team:landing-procedure','MANDATORY ACTIONS','p.5 each player must place one die on Axis and one on Engines every round'),
('sky-team:landing:axis','publisher:scorpion:sky-team:landing-procedure','AXIS','p.5 axis movement and spin loss condition'),
('sky-team:landing:engines','publisher:scorpion:sky-team:landing-procedure','ENGINES','p.6 speed thresholds, approach movement, collision and overshoot'),
('sky-team:landing:gear','publisher:scorpion:sky-team:landing-procedure','LANDING GEAR','p.7 deployment and aerodynamics marker effect'),
('sky-team:landing:radio','publisher:scorpion:sky-team:landing-procedure','RADIO','p.7 clearing traffic by die value'),
('sky-team:landing:flaps','publisher:scorpion:sky-team:landing-procedure','FLAPS','p.8 ordered deployment and aerodynamics marker effect'),
('sky-team:landing:coffee','publisher:scorpion:sky-team:landing-procedure','CONCENTRATION','p.8 coffee-token creation and die-value modification'),
('sky-team:landing:brakes','publisher:scorpion:sky-team:landing-procedure','BRAKES','p.9 ordered brake deployment and final-round requirement'),
('sky-team:landing:end-round','publisher:scorpion:sky-team:landing-procedure','END OF ROUND','p.9 descend 1,000 feet, recover dice, check airport/altitude timing'),
('sky-team:landing:final','publisher:scorpion:sky-team:landing-procedure','FINAL TURN - LANDING','p.11 four simultaneous landing victory conditions')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='sky-team' LIMIT 1;
  IF v_game_id IS NULL OR v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Sky Team Game/Work row is required'; END IF;

  UPDATE public.games SET
    title='Sky Team',title_ja='スカイチーム',title_en='Sky Team',
    description='機長と副操縦士がダイスを交互に配置し、機体の姿勢・速度・交通・フラップ・着陸装置・ブレーキを管理して安全な着陸を目指す2人専用協力ゲーム。',
    summary='相談できる時間と無言で操縦する時間を切り替えながら、モントリオールへの着陸条件を2人で整える。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://sugorokuya.jp/p/sky-team',
    source_url='https://www.scorpionmasque.com/en/sky-team',official_url='https://sugorokuya.jp/p/sky-team',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='スカイチーム 日本語版（2024年6月）',language_code='ja',publisher='すごろくや / Le Scorpion Masqué',
    source_revision='Scorpion Masqué Landing Procedure 2023-06-06 + Sugorokuya Japanese edition identity; audited 2026-08-24',
    min_players=2,max_players=2,play_time=20,min_age=12,published_year=2024,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id
    AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='スカイチーム 日本語版（2024年6月）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='landing-procedure-2023-06-06-ja-2024-06'
    AND COALESCE(variant_label,'')=''
    AND version=1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','スカイチーム 日本語版（2024年6月）',
      'Scorpion Masqué Landing Procedure 2023-06-06 + Sugorokuya Japanese edition identity; audited 2026-08-24',
      true,'landing-procedure-2023-06-06-ja-2024-06','physical','すごろくや / Le Scorpion Masqué','active','source_bound',
      ARRAY['localizer:sugorokuya:sky-team:product','publisher:scorpion:sky-team:landing-procedure','publisher:scorpion:sky-team:product']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,schema_version='1.0',
      source_revision='Scorpion Masqué Landing Procedure 2023-06-06 + Sugorokuya Japanese edition identity; audited 2026-08-24',
      is_active=true,publisher_name='すごろくや / Le Scorpion Masqué',status='active',verification_status='source_bound',
      source_ids=ARRAY['localizer:sugorokuya:sky-team:product','publisher:scorpion:sky-team:landing-procedure','publisher:scorpion:sky-team:product']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.montreal-basic','setup','基本ゲームではコントロールパネルを2人の間に置き、機体傾度を水平、各スイッチを初期位置にする。青・オレンジの空気力学マーカーとブレーキを指定位置に置き、機長は青4個、副操縦士はオレンジ4個のダイスを受け取る。高度は6000フィート、進入トラックはYULモントリオール・トリドーを使用し、交通・振り直し・コーヒーを準備する。上級モジュール用の部品は基本ゲームでは使わない。',10,'source_bound','sky-team:rule:setup.montreal-basic','sky-team:binding:setup.montreal-basic','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:setup','{"scope":"base_montreal_only"}'::jsonb),
  (v_ruleset_id,'round.communication','turn','ゲームは7ラウンドで、各ラウンドは作戦相談とダイスロール、ダイス配置、ラウンド終了の3段階。ラウンド開始時は作戦を相談できるがダイスの出目を前提にした指示はできず、ダイスをついたての裏で振った後はルール誤りの訂正を除いてラウンド終了まで会話しない。',20,'source_bound','sky-team:rule:round.communication','sky-team:binding:round.communication','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:round','{}'::jsonb),
  (v_ruleset_id,'turn.dice-placement','action','開始プレイヤーから交互に、手元のダイスを1個だけ空いているアクションスペースへ置く。機長は青、副操縦士はオレンジの色制限に従い、指定がある場所では出目の条件にも従う。',30,'source_bound','sky-team:rule:turn.dice-placement','sky-team:binding:turn.dice-placement','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:placement','{}'::jsonb),
  (v_ruleset_id,'round.mandatory-actions','condition','毎ラウンド、機長と副操縦士はそれぞれ機体傾度とエンジンに1個ずつダイスを置かなければならない。ラウンド終了時にどちらかの色のダイスが機体傾度またはエンジンに無ければ即座に敗北する。',40,'source_bound','sky-team:rule:round.mandatory-actions','sky-team:binding:round.mandatory-actions','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:mandatory','{}'::jsonb),
  (v_ruleset_id,'action.axis','action','機体傾度に2個目のダイスを置いたら2個の差だけ大きい出目を置いた側へ機体を傾け、その傾きはラウンドをまたいで維持する。傾度矢印がスピン位置に達するか越えると即座に敗北する。',50,'source_bound','sky-team:rule:action.axis','sky-team:binding:action.axis','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:axis','{}'::jsonb),
  (v_ruleset_id,'action.engines','action','エンジンに2個目のダイスを置いた時点で合計を速度とする。速度が青の空気力学マーカー未満なら進入トラックは動かず、2つのマーカー間なら1マス、オレンジのマーカーより大きければ2マス進む。進む際に現在位置へ飛行機コマが残っていれば衝突、空港を越えて進めばオーバーシュートとなり敗北する。',60,'source_bound','sky-team:rule:action.engines','sky-team:binding:action.engines','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:engines','{}'::jsonb),
  (v_ruleset_id,'action.radio','action','無線に置いたダイスの出目ぶん、現在位置を1として進入トラック上のマスを数え、そのマスに飛行機コマがあれば1個を直ちに取り除く。該当マスに飛行機コマが無い場合は効果がない。',70,'source_bound','sky-team:rule:action.radio','sky-team:binding:action.radio','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:radio','{}'::jsonb),
  (v_ruleset_id,'action.landing-gear','action','着陸装置は各スペースの出目条件を満たして展開し、順番は任意。初めて展開した各スイッチを緑にし、青の空気力学マーカーを直ちに1マス進める。ゲーム終了時にはすべての着陸装置が緑でなければならない。',80,'source_bound','sky-team:rule:action.landing-gear','sky-team:binding:action.landing-gear','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:gear','{}'::jsonb),
  (v_ruleset_id,'action.flaps','action','フラップは出目条件を満たし、1/2、2/3、3/4、4/5の順に展開する。展開したスイッチを緑にし、オレンジの空気力学マーカーを直ちに1マス進める。ゲーム終了時にはすべてのフラップが緑でなければならない。',90,'source_bound','sky-team:rule:action.flaps','sky-team:binding:action.flaps','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:flaps','{}'::jsonb),
  (v_ruleset_id,'action.concentration','action','集中スペースにはどちらのプレイヤーも任意の出目を置け、直ちにコーヒーコマを1個得る。コーヒーは最大3個まで保持でき、ダイスを置くとき1個につき出目を1増減できるが、変更後の値は1～6の範囲に限る。',100,'source_bound','sky-team:rule:action.concentration','sky-team:binding:action.concentration','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:coffee','{}'::jsonb),
  (v_ruleset_id,'action.brakes','action','ブレーキは機長だけが2、4、6の順に対応する出目で展開し、展開するたび赤のブレーキマーカーを1マス進める。全てを展開する必要はないが、最終ラウンドではエンジン2個の合計速度がブレーキ値より小さくなければならない。',110,'source_bound','sky-team:rule:action.brakes','sky-team:binding:action.brakes','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:brakes','{}'::jsonb),
  (v_ruleset_id,'round.end','turn','8個すべてのダイスを配置したら会話を再開し、高度トラックを1マス（1000フィート）下げてダイスを回収する。空港と機体の高度が同時に着陸位置へ到達したら最終着陸判定へ進み、機体だけが先に高度0へ到達して空港へ着いていなければ墜落として敗北する。',120,'source_bound','sky-team:rule:round.end','sky-team:binding:round.end','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:end-round','{}'::jsonb),
  (v_ruleset_id,'game.victory','condition','最終ラウンド終了時、進入トラック上に飛行機コマが無く、フラップと着陸装置の全スイッチが緑、機体が完全に水平、かつ最終ラウンドに置いたエンジンダイスの合計速度がブレーキ値より小さければ着陸成功で勝利する。',130,'source_bound','sky-team:rule:game.victory','sky-team:binding:game.victory','https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf','sky-team:landing:final','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT
    'sky-team:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"base_montreal_landing_procedure_only"}'::jsonb
  FROM public.rule_nodes
  WHERE rule_set_id=v_ruleset_id AND rule_id IN(
    'setup.montreal-basic','round.communication','turn.dice-placement','round.mandatory-actions','action.axis','action.engines',
    'action.radio','action.landing-gear','action.flaps','action.concentration','action.brakes','round.end','game.victory'
  )
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
  ('sky-team:binding:setup.montreal-basic','sky-team:rule:setup.montreal-basic','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:setup','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:round.communication','sky-team:rule:round.communication','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:round','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:turn.dice-placement','sky-team:rule:turn.dice-placement','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:placement','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:round.mandatory-actions','sky-team:rule:round.mandatory-actions','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:mandatory','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:action.axis','sky-team:rule:action.axis','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:axis','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:action.engines','sky-team:rule:action.engines','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:engines','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:action.radio','sky-team:rule:action.radio','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:radio','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:action.landing-gear','sky-team:rule:action.landing-gear','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:gear','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:action.flaps','sky-team:rule:action.flaps','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:flaps','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:action.concentration','sky-team:rule:action.concentration','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:coffee','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:action.brakes','sky-team:rule:action.brakes','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:brakes','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:round.end','sky-team:rule:round.end','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:end-round','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('sky-team:binding:game.victory','sky-team:rule:game.victory','publisher:scorpion:sky-team:landing-procedure','sky-team:landing:final','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,
    reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;
END $$;

COMMIT;

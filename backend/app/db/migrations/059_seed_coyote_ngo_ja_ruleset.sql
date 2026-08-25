BEGIN;

-- Canonical scope: New Games Order Japanese Coyote physical base game.
-- The current publisher product page establishes the Japanese 2–10 player product; the embedded
-- Japanese rulebook is the rule authority. Optional special-rule cards are excluded from this base RuleSet.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:ngo:coyote:product-ja','https://www.newgamesorder.jp/games/coyote','コヨーテ — ニューゲームズオーダー公式商品ページ','publisher_product_page','ニューゲームズオーダー','physical','ja','current-product-page','{"authority":"publisher","audit_date":"2026-08-25","scope":"japanese_product_identity_and_official_faq"}'::jsonb),
('publisher:ngo:coyote:rulebook-ja','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','コヨーテ ルール — ニューゲームズオーダー日本語ルール','publisher_rulebook','ニューゲームズオーダー','physical','ja','hosted-2026-02-20','{"authority":"publisher","audit_date":"2026-08-25","scope":"base_game_rules","file_modified":"2026-02-20","booklet_copyright":"2014"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('coyote:product:identity','publisher:ngo:coyote:product-ja',NULL,'コヨーテ','Coyote; 2–10 players; age 10+; 15–30 minutes; New Games Order current Japanese product'),
('coyote:product:fox-faq','publisher:ngo:coyote:product-ja',NULL,'よくあるご質問','if multiple cards share the maximum value, Fox changes only one of those cards to 0'),
('coyote:rules:setup-cards','publisher:ngo:coyote:rulebook-ja',2,'ゲームの準備 / ナンバーカードの持ち方','shuffle number cards; deal one face down to each player; keep own face hidden and show it to all others'),
('coyote:rules:setup-life','publisher:ngo:coyote:rulebook-ja',2,'ライフカードの見方','each player takes one life card; two substitute figures plus self represent three remaining lives'),
('coyote:rules:first-declaration','publisher:ngo:coyote:rulebook-ja',2,'ゲームの手順','first player declares an integer of at least 1 as an estimate of the total Coyote value'),
('coyote:rules:raise-or-coyote','publisher:ngo:coyote:rulebook-ja',2,'ゲームの手順','clockwise, declare a larger number than the previous declaration or call Coyote'),
('coyote:rules:resolve-total','publisher:ngo:coyote:rulebook-ja',2,'ゲームの手順','after Coyote, reveal all number cards, total number-card values, then apply special-card calculations'),
('coyote:rules:resolve-winner','publisher:ngo:coyote:rulebook-ja',2,'ゲームの手順','if previous declaration exceeds actual total the Coyote caller wins; otherwise the declarer wins'),
('coyote:rules:damage-next-round','publisher:ngo:coyote:rulebook-ja',2,'ゲームの手順','loser takes damage; used cards go to discard; draw new cards; when deck is empty reshuffle discard; loser starts next round'),
('coyote:rules:game-end','publisher:ngo:coyote:rulebook-ja',2,'ゲームの終了','a player is eliminated after three losses when life reaches 0; last surviving player wins'),
('coyote:rules:soldier-ghost','publisher:ngo:coyote:rulebook-ja',3,'ナンバーカードの説明','soldier cards subtract their printed value; ghost card adds 0'),
('coyote:rules:chief-fox','publisher:ngo:coyote:rulebook-ja',3,'ナンバーカードの説明','Chief doubles all basic-card values; Fox changes the maximum Coyote-card value in the round to 0'),
('coyote:rules:night-question','publisher:ngo:coyote:rulebook-ja',3,'ナンバーカードの説明','Night adds 0 and causes all number cards to be reshuffled after calculation; Question draws one additional number card and adds it to the calculation')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='coyote' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Coyote canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Coyote Work row is required'; END IF;

  UPDATE public.games SET
    title='コヨーテ',title_ja='コヨーテ',title_en='Coyote',
    description='自分だけが見えないナンバーカードを掲げ、他プレイヤーのカードと宣言から場の合計値を推理して数字を上げるか「コヨーテ！」を宣言するブラフゲーム。',
    summary='自分のカードは見ずに他人のカードだけを見て、時計回りに合計値の予想を上げる。前の宣言が実際の合計を超えたと思ったら「コヨーテ！」で勝負する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://www.newgamesorder.jp/games/coyote',
    source_url='https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view',
    official_url='https://www.newgamesorder.jp/games/coyote',source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='コヨーテ（ニューゲームズオーダー日本語版）',language_code='ja',publisher='ニューゲームズオーダー',
    source_revision='New Games Order current Japanese product page and hosted Japanese rulebook (file modified 2026-02-20; booklet ©2014); optional special-rule cards excluded; audited 2026-08-25',
    min_players=2,max_players=10,play_time=30,min_age=10,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='コヨーテ（ニューゲームズオーダー日本語版）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='ngo-ja-rulebook-2026-02-20'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','コヨーテ（ニューゲームズオーダー日本語版）',
      'New Games Order current Japanese product page and hosted Japanese rulebook (file modified 2026-02-20; booklet ©2014); optional special-rule cards excluded; audited 2026-08-25',
      true,'ngo-ja-rulebook-2026-02-20','physical','ニューゲームズオーダー','active','source_bound',
      ARRAY['publisher:ngo:coyote:product-ja','publisher:ngo:coyote:rulebook-ja']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='New Games Order current Japanese product page and hosted Japanese rulebook (file modified 2026-02-20; booklet ©2014); optional special-rule cards excluded; audited 2026-08-25',
      publisher_name='ニューゲームズオーダー',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:ngo:coyote:product-ja','publisher:ngo:coyote:rulebook-ja']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'setup.number-card','setup','ナンバーカードをよくシャッフルし、各プレイヤーに1枚ずつ裏向きで配り、残りを山札にする。自分のカードの表は見ず、他の全員から見えるように掲げる。',10,'source_bound','coyote:rule:setup.number-card','coyote:binding:setup.number-card','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:setup-cards','{}'::jsonb),
  (v_ruleset_id,'setup.life-card','setup','各プレイヤーはライフカードを1枚受け取り、身代わり人形2体が見える状態で始める。身代わり人形2体と自分を合わせた3が開始時の残りライフになる。',20,'source_bound','coyote:rule:setup.life-card','coyote:binding:setup.life-card','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:setup-life','{}'::jsonb),
  (v_ruleset_id,'turn.first-declaration','turn','最初のプレイヤーは、他プレイヤーに見えているカードから場の合計値を推理し、1以上の整数を宣言する。0は宣言できない。',30,'source_bound','coyote:rule:turn.first-declaration','coyote:binding:turn.first-declaration','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:first-declaration','{}'::jsonb),
  (v_ruleset_id,'turn.raise-or-coyote','turn','以後は時計回りに、直前の宣言より大きい整数を宣言するか、直前の宣言が実際の合計より大きいと思ったら「コヨーテ！」と宣言する。',40,'source_bound','coyote:rule:turn.raise-or-coyote','coyote:binding:turn.raise-or-coyote','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:raise-or-coyote','{}'::jsonb),
  (v_ruleset_id,'resolve.coyote-total','effect','「コヨーテ！」が宣言されたら全員のナンバーカードを表にして、まず基本カードの数値を合計し、その後に特殊カードの効果を計算して実際の合計値を決める。',50,'source_bound','coyote:rule:resolve.coyote-total','coyote:binding:resolve.coyote-total','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:resolve-total','{}'::jsonb),
  (v_ruleset_id,'resolve.coyote-winner','effect','直前に宣言された数字が実際の合計値を超えていた場合は「コヨーテ！」を宣言したプレイヤーが勝ち、超えていなければ直前に数字を宣言したプレイヤーが勝つ。',60,'source_bound','coyote:rule:resolve.coyote-winner','coyote:binding:resolve.coyote-winner','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:resolve-winner','{}'::jsonb),
  (v_ruleset_id,'round.damage','effect','勝負に負けたプレイヤーはダメージを1回受け、ライフカードで残りライフを1減らす。',70,'source_bound','coyote:rule:round.damage','coyote:binding:round.damage','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:damage-next-round','{}'::jsonb),
  (v_ruleset_id,'round.next','turn','使用したナンバーカードを捨て札にして新しいカードを山札から1枚ずつ取り、直前の勝負で負けたプレイヤーから次の回を始める。山札がなくなったら捨て札をシャッフルして新しい山札にする。',80,'source_bound','coyote:rule:round.next','coyote:binding:round.next','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:damage-next-round','{}'::jsonb),
  (v_ruleset_id,'special.soldier-ghost','effect','兵隊カードは表示された負の数だけ合計値を減らし、おばけカードは合計値に加えない。',90,'source_bound','coyote:rule:special.soldier-ghost','coyote:binding:special.soldier-ghost','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:soldier-ghost','{}'::jsonb),
  (v_ruleset_id,'special.chief-fox','effect','酋長カードはすべての基本カードの数値を2倍にする。キツネカードはその回に出た最大のコヨーテカード1枚の数値を0にし、最大値が複数枚あっても0になるのは1枚だけ。',100,'source_bound','coyote:rule:special.chief-fox','coyote:binding:special.chief-fox','https://www.newgamesorder.jp/games/coyote','coyote:product:fox-faq','{}'::jsonb),
  (v_ruleset_id,'special.night-question','effect','夜カードは合計値に加えず、計算終了後にすべてのナンバーカードを合わせて山札を作り直す。ほらあなカードが出た場合は、計算時に山札からナンバーカードを1枚追加でめくり、その数を合計に加える。',110,'source_bound','coyote:rule:special.night-question','coyote:binding:special.night-question','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:night-question','{}'::jsonb),
  (v_ruleset_id,'game.end','game_end','3回負けてライフが0になったプレイヤーは脱落し、最後まで生き残ったプレイヤーが勝者になる。',120,'source_bound','coyote:rule:game.end','coyote:binding:game.end','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:game-end','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'coyote:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-25","scope":"coyote_ngo_japanese_base"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'coyote:binding:'||rn.rule_id,'coyote:rule:'||rn.rule_id,
    CASE WHEN rn.rule_id='special.chief-fox' THEN 'publisher:ngo:coyote:product-ja' ELSE 'publisher:ngo:coyote:rulebook-ja' END,
    rn.source_locator,'supports','{"review":"publisher_primary_source"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 12 THEN RAISE EXCEPTION 'Coyote source-bound RuleNode count must be 12'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 12 THEN RAISE EXCEPTION 'Coyote accepted Claim count must be 12'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 12 THEN RAISE EXCEPTION 'Coyote supporting EvidenceBinding count must be 12'; END IF;
END $$;

COMMIT;

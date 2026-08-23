BEGIN;

-- Canonical scope: Arclight's 2019 Japanese physical edition of Brass: Birmingham,
-- using Roxley Games' 2018-11-20 Brass: Birmingham rulebook as gameplay authority.
-- Brass: Lancashire, later collector packaging, and third-party digital implementations are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('localizer:arclight:brass-birmingham:product','https://arclightgames.jp/product/%E3%83%96%E3%83%A9%E3%82%B9%E3%83%90%E3%83%BC%E3%83%9F%E3%83%B3%E3%82%AC%E3%83%A0/','ブラス：バーミンガム 完全日本語版','localized_product_page','アークライト','physical','ja','jp-edition-2019-11-28','{"authority":"official_localizer","audit_date":"2026-08-24","scope":"japanese_product_identity"}'::jsonb),
('publisher:roxley:brass-birmingham:rulebook','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','Brass: Birmingham Rulebook','publisher_rulebook','Roxley Games','physical','en','2018.11.20','{"authority":"publisher","audit_date":"2026-08-24","scope":"brass_birmingham_base_game"}'::jsonb),
('publisher:roxley:brass-birmingham:product','https://roxley.com/products/brass-birmingham','Brass: Birmingham','publisher_product_page','Roxley Games','physical','en','current-product-page','{"authority":"publisher","audit_date":"2026-08-24","scope":"product_identity_and_current_rulebook_link"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('brass-birmingham:arclight:product','localizer:arclight:brass-birmingham:product','商品概要','2019-11-28発売、2–4人、60–120分、14歳以上、原版メーカー Roxley Games'),
('brass-birmingham:rulebook:setup','publisher:roxley:brass-birmingham:rulebook','BOARD SETUP / PLAYER AREA SETUP','board/player setup; £17, income 10, 8-card hand, player-count removals'),
('brass-birmingham:rulebook:goal','publisher:roxley:brass-birmingham:rulebook','THE GOAL / ROUNDS','two eras; VP scored at end of each era; round counts by player count'),
('brass-birmingham:rulebook:turn','publisher:roxley:brass-birmingham:rulebook','PLAYER TURNS','two actions normally; one action in first Canal Era round; discard one card per action'),
('brass-birmingham:rulebook:turn-order','publisher:roxley:brass-birmingham:rulebook','END OF ROUND','next-round order by least money spent; ties preserve relative order; income step'),
('brass-birmingham:rulebook:build','publisher:roxley:brass-birmingham:rulebook','BUILD ACTION','location/industry card placement, tile cost, required coal/iron'),
('brass-birmingham:rulebook:network','publisher:roxley:brass-birmingham:rulebook','NETWORK ACTION','Canal £3; Rail £5 + coal; two Rails £15 + beer + coal'),
('brass-birmingham:rulebook:develop','publisher:roxley:brass-birmingham:rulebook','DEVELOP ACTION','remove one or two lowest-level industry tiles and consume iron'),
('brass-birmingham:rulebook:sell','publisher:roxley:brass-birmingham:rulebook','SELL ACTION','sell cotton/manufactured goods/pottery to connected merchant; consume beer when required'),
('brass-birmingham:rulebook:loan','publisher:roxley:brass-birmingham:rulebook','LOAN ACTION','take £30; move income marker three income levels backward; floor -10'),
('brass-birmingham:rulebook:scout','publisher:roxley:brass-birmingham:rulebook','SCOUT ACTION','discard three cards total for one Wild Industry and one Wild Location; forbidden with Wild already in hand'),
('brass-birmingham:rulebook:coal','publisher:roxley:brass-birmingham:rulebook','CONSUMING COAL','consume closest connected coal first, otherwise Coal Market'),
('brass-birmingham:rulebook:iron','publisher:roxley:brass-birmingham:rulebook','CONSUMING IRON','connection not required; use any unflipped Iron Works before Iron Market'),
('brass-birmingham:rulebook:beer','publisher:roxley:brass-birmingham:rulebook','CONSUMING BEER','own Brewery need not be connected; other Brewery must be connected; merchant beer only when selling to that merchant'),
('brass-birmingham:rulebook:era-end','publisher:roxley:brass-birmingham:rulebook','END OF ERA MAINTENANCE / WINNING THE GAME','score links and flipped industries; Canal removes level-1 board industries; Rail scoring determines winner')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='brass-birmingham' LIMIT 1;
  IF v_game_id IS NULL OR v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Brass: Birmingham Game/Work row is required'; END IF;

  UPDATE public.games SET
    title='Brass: Birmingham',title_ja='ブラス：バーミンガム',title_en='Brass: Birmingham',
    description='産業革命期のイングランド中西部で産業施設と運河・鉄道網を築き、2つの時代を通じて勝利点を競う経済戦略ゲーム。',
    summary='カードを使って建設・ネットワーク・開発・売却・借入・偵察を行い、運河時代と鉄道時代の終わりにリンクと稼働済み産業を得点する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://arclightgames.jp/product/%E3%83%96%E3%83%A9%E3%82%B9%E3%83%90%E3%83%BC%E3%83%9F%E3%83%B3%E3%82%AC%E3%83%A0/',
    source_url='https://roxley.com/products/brass-birmingham',official_url='https://arclightgames.jp/product/%E3%83%96%E3%83%A9%E3%82%B9%E3%83%90%E3%83%BC%E3%83%9F%E3%83%B3%E3%82%AC%E3%83%A0/',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='ブラス：バーミンガム 完全日本語版（2019年11月28日）',language_code='ja',publisher='アークライト / Roxley Games',
    source_revision='Roxley Brass: Birmingham Rulebook 2018.11.20 + Arclight Japanese edition identity; audited 2026-08-24',
    min_players=2,max_players=4,play_time=120,min_age=14,published_year=2019,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id
    AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='ブラス：バーミンガム 完全日本語版（2019年11月28日）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='roxley-2018.11.20-ja-2019-11-28'
    AND COALESCE(variant_label,'')=''
    AND version=1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','ブラス：バーミンガム 完全日本語版（2019年11月28日）',
      'Roxley Brass: Birmingham Rulebook 2018.11.20 + Arclight Japanese edition identity; audited 2026-08-24',
      true,'roxley-2018.11.20-ja-2019-11-28','physical','アークライト / Roxley Games','active','source_bound',
      ARRAY['localizer:arclight:brass-birmingham:product','publisher:roxley:brass-birmingham:rulebook','publisher:roxley:brass-birmingham:product']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,schema_version='1.0',
      source_revision='Roxley Brass: Birmingham Rulebook 2018.11.20 + Arclight Japanese edition identity; audited 2026-08-24',
      is_active=true,publisher_name='アークライト / Roxley Games',status='active',verification_status='source_bound',
      source_ids=ARRAY['localizer:arclight:brass-birmingham:product','publisher:roxley:brass-birmingham:rulebook','publisher:roxley:brass-birmingham:product']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.base','setup','プレイヤー人数に応じて対象外のカードと商人タイルを除外し、石炭市場・鉄市場・商人のビールを準備する。各プレイヤーは£17、個人ボード、産業タイル、リンクタイルを受け取り、VPを0、収入マーカーを10に置き、8枚を手札として引き、さらに1枚を裏向きの捨て札として置く。',10,'source_bound','brass-birmingham:rule:setup.base','brass-birmingham:binding:setup.base','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:setup','{}'::jsonb),
  (v_ruleset_id,'game.two-eras','condition','ゲームは運河時代（1770–1830）と鉄道時代（1830–1870）の2時代で行う。各時代は山札と全員の手札が尽きるまでラウンドを続け、4人戦は8、3人戦は9、2人戦は10ラウンドとなる。',20,'source_bound','brass-birmingham:rule:game.two-eras','brass-birmingham:binding:game.two-eras','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:goal','{}'::jsonb),
  (v_ruleset_id,'turn.actions','turn','通常の手番では合計2アクションを行い、各アクションごとに手札から1枚を捨てる。例外として運河時代の第1ラウンドだけは各プレイヤー1アクションで、手番終了後は可能なら手札を8枚まで補充する。',30,'source_bound','brass-birmingham:rule:turn.actions','brass-birmingham:binding:turn.actions','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:turn','{}'::jsonb),
  (v_ruleset_id,'round.turn-order','turn','ラウンド終了時、次ラウンドの手番順はそのラウンドに使った金額が少ないプレイヤーから並べる。同額なら直前の相対順を維持し、その後に各プレイヤーの現在の収入レベルに従って収入処理を行う。',40,'source_bound','brass-birmingham:rule:round.turn-order','brass-birmingham:binding:round.turn-order','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:turn-order','{}'::jsonb),
  (v_ruleset_id,'action.build','action','建設ではロケーションカードまたは産業カード等の有効なカードを捨て、個人ボード上でその産業の最も低いレベルのタイルを適切な建設枠へ置く。表示された金額を支払い、必要なら石炭・鉄を消費する。',50,'source_bound','brass-birmingham:rule:action.build','brass-birmingham:binding:action.build','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:build','{}'::jsonb),
  (v_ruleset_id,'action.network','action','ネットワークでは自分のネットワークに隣接する未使用の路線へリンクを置く。運河時代は運河1本を£3で建設できる。鉄道時代は鉄道1本につき石炭1個を消費し、1本なら£5、同じアクションで2本なら合計£15に加えて醸造所のビール1個を消費する。',60,'source_bound','brass-birmingham:rule:action.network','brass-birmingham:binding:action.network','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:network','{}'::jsonb),
  (v_ruleset_id,'action.develop','action','開発では個人ボード上の産業タイルを1枚または2枚取り除き、取り除いたタイル1枚につき鉄1個を消費する。各産業では最も低いレベルのタイルから取り除く。',70,'source_bound','brass-birmingham:rule:action.develop','brass-birmingham:binding:action.develop','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:develop','{}'::jsonb),
  (v_ruleset_id,'action.sell','action','売却では自分の未裏返しの綿工場・製造所・窯元を、その商品を受け入れる接続済み商人へ売る。産業タイルに示された量のビールを必要に応じて消費し、条件を満たした産業タイルを裏返す。1回の売却アクションで条件を満たす複数の産業を続けて売却できる。',80,'source_bound','brass-birmingham:rule:action.sell','brass-birmingham:binding:action.sell','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:sell','{}'::jsonb),
  (v_ruleset_id,'action.loan','action','借入では銀行から£30を受け取り、収入マーカーを3スペースではなく3収入レベル後退させ、その下側レベルの最も高いスペースに置く。収入レベルが-10を下回る借入はできない。',90,'source_bound','brass-birmingham:rule:action.loan','brass-birmingham:binding:action.loan','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:loan','{}'::jsonb),
  (v_ruleset_id,'action.scout','action','偵察では通常のアクション用カード1枚に加えてさらに2枚、合計3枚を捨て、ワイルド産業カード1枚とワイルドロケーションカード1枚を得る。すでに手札にワイルドカードがある場合は偵察できない。',100,'source_bound','brass-birmingham:rule:action.scout','brass-birmingham:binding:action.scout','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:scout','{}'::jsonb),
  (v_ruleset_id,'resource.coal','condition','石炭を消費する場合、その場所は石炭供給源へ接続されていなければならない。利用可能な石炭鉱山が接続されている場合は最も近い石炭を優先し、利用できる鉱山が無ければ石炭市場から安い価格順に購入する。',110,'source_bound','brass-birmingham:rule:resource.coal','brass-birmingham:binding:resource.coal','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:coal','{}'::jsonb),
  (v_ruleset_id,'resource.iron','condition','鉄を消費する産業は鉄供給源へ接続している必要がない。盤上に鉄が残る未裏返しの製鉄所がある間は任意の製鉄所から無料で消費し、無くなった後は鉄市場から安い価格順に購入する。',120,'source_bound','brass-birmingham:rule:resource.iron','brass-birmingham:binding:resource.iron','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:iron','{}'::jsonb),
  (v_ruleset_id,'resource.beer','condition','自分の醸造所のビールは接続なしで消費できる。他プレイヤーの醸造所のビールは必要な場所から接続されている場合だけ使える。商人脇のビールは、その商人へ売却するときだけ消費できる。',130,'source_bound','brass-birmingham:rule:resource.beer','brass-birmingham:binding:resource.beer','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:beer','{}'::jsonb),
  (v_ruleset_id,'game.scoring','condition','各時代の終了時、まず各リンクについて両端の場所に表示されたリンク得点アイコンを数えてVPを得てリンクを除去し、その後に裏返った産業タイルのVPを得る。運河時代終了時には盤上のレベル1産業を除去する。鉄道時代の得点後、VP最多のプレイヤーが勝ち、同点は収入、次に所持金で判定する。',140,'source_bound','brass-birmingham:rule:game.scoring','brass-birmingham:binding:game.scoring','https://files.roxley.com/Brass-Birmingham-Rulebook-2018.11.20-highlights.pdf','brass-birmingham:rulebook:era-end','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT
    'brass-birmingham:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"brass_birmingham_base_game"}'::jsonb
  FROM public.rule_nodes
  WHERE rule_set_id=v_ruleset_id AND rule_id IN(
    'setup.base','game.two-eras','turn.actions','round.turn-order','action.build','action.network','action.develop',
    'action.sell','action.loan','action.scout','resource.coal','resource.iron','resource.beer','game.scoring'
  )
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
  ('brass-birmingham:binding:setup.base','brass-birmingham:rule:setup.base','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:setup','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:game.two-eras','brass-birmingham:rule:game.two-eras','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:goal','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:turn.actions','brass-birmingham:rule:turn.actions','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:turn','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:round.turn-order','brass-birmingham:rule:round.turn-order','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:turn-order','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:action.build','brass-birmingham:rule:action.build','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:build','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:action.network','brass-birmingham:rule:action.network','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:network','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:action.develop','brass-birmingham:rule:action.develop','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:develop','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:action.sell','brass-birmingham:rule:action.sell','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:sell','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:action.loan','brass-birmingham:rule:action.loan','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:loan','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:action.scout','brass-birmingham:rule:action.scout','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:scout','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:resource.coal','brass-birmingham:rule:resource.coal','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:coal','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:resource.iron','brass-birmingham:rule:resource.iron','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:iron','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:resource.beer','brass-birmingham:rule:resource.beer','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:beer','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('brass-birmingham:binding:game.scoring','brass-birmingham:rule:game.scoring','publisher:roxley:brass-birmingham:rulebook','brass-birmingham:rulebook:era-end','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,
    reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;
END $$;

COMMIT;
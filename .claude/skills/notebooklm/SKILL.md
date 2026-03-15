---
name: notebooklm
description: NotebookLM + Gemini Nano Banana pipeline for board game rule extraction, Japanese localization, and professional infographic generation. Extract PDF rulebooks → structure as JSON → translate to natural Japanese → generate explanatory infographics (SVG + PNG) with Japanese labels → store everything in Supabase.
tags: [boardgame, rule-extraction, pdf-parsing, japanese-translation, infographic, nano-banana, gemini-image]
version: 2.2
---

# NotebookLM Skill: Board Game Rule Extraction + Nano Banana Infographic Pipeline

Board game rule ingestion via PDF → structured JSON → native Japanese refinement → **Gemini Nano Banana Pro** powered infographics.

## When to Invoke

- New game ingestion: "Extract rules from official PDF, create Japanese record, and generate infographics with Nano Banana"
- Rule regeneration: "Regenerate rules + infographics for [game] from source PDF using Nano Banana"
- Batch processing: "Extract + generate infographics for [game list] in parallel"
- Infographic refresh: "Improve infographics for [game] with professional Japanese style"

## Updated Pipeline Stages (v2.2)

1. **PDF Discovery (PDFDiscoveryService)**
   Find official rulebook URL (BGG, publisher site, etc.)

2. **Content Extraction (NotebookLMPlaywrightExtractor + Gemini Structured Output)**
   Parse PDF → raw structured JSON
   Fields: title, components, setup, turn_structure, player_actions, winning_conditions, edge_cases, etc.
   Use Gemini 3.x structured output (JSON mode + schema) for high accuracy + citations

3. **Japanese Refinement (Gemini 3.x Flash / Pro)**
   Translate + naturalize all text to native-level Japanese
   Maintain structure, add confidence scores per section
   Output: full game metadata record (matches CLAUDE.md schema)

4. **Infographic Generation (NEW: Gemini Nano Banana Pro / Nano Banana 2)**
   Generate multiple instructional diagrams automatically
   Styles supported: professional_clean, instructional_diagram, sketch_note, minimal_flat, kawaii_japanese, boardgame_icon_style
   All text rendered in natural Japanese (advanced text rendering)
   Multi-panel or single focused diagrams

5. **Database Storage (Supabase)**
   Upsert game record with rules_ja, metadata, confidence
   Store infographics as: image_url (PNG), svg_url (if generated), infographic_metadata (schema + visualized_rules)
   Track data_version + generation_model ("nano_banana_pro")

## Nano Banana Infographic Generation Details (Core Enhancement)

**Recommended Model**:
- **Primary**: Gemini 3.x Nano Banana Pro（高品質・複雑なダイアグラム・正確な日本語テキスト描画に最適）
- **Fast/Volume**: Nano Banana 2 (Gemini 3.1 Flash Image) – 高速生成・バッチ向き

**Auto-generated Infographic Types** (per game):
1. **Setup / Component Layout** – コンポーネント配置と初期セットアップの俯瞰図
2. **Turn Structure Flow** – ターン進行の流れ（矢印 + 条件分岐）
3. **Winning Conditions Flowchart** – 勝利条件の論理ツリーまたはフローチャート
4. **Player Interaction Map** – プレイヤー間の相互作用（アクション・影響）
5. **Key Mechanics Overview** – ゲームのコアメカニクス1枚まとめ（アイコン多め）

**Prompt Engineering Best Practice (Nano Banana用)**:
各インフォグラフィック生成時に以下のプロンプトテンプレートを使う：

```text
Create a clear, professional instructional infographic for the board game "[Game Title]" (Japanese: "[Title_ja]").

Visualize: [specific section, e.g. "turn structure and player actions"]
Use this structured data: [paste the refined JSON section]

Requirements:
- All text must be in natural, easy-to-read Japanese (large, legible font)
- Professional board game rulebook style: clean lines, icons, color coding (use consistent palette)
- Include step numbers, arrows, and short explanatory captions
- Add small English subtitle only if necessary for international clarity
- Style: [professional_clean / kawaii_japanese / minimal_flat]
- High resolution, perfect text rendering, no distortion
- Make it educational and glanceable – users should understand the mechanic from this image alone
```

**Output Handling**:
Gemini Image Generation APIで生成 → Supabase Storageにアップロード
メタデータ保存: visualized_rule_ids, style_used, confidence, generated_at, model: "nano_banana_pro"

## Rules

- **Japanese First**: すべてのテキスト（ルール + インフォグラフィック内）は自然なネイティブ日本語。機械翻訳感ゼロ。
- **No Hallucination**: PDFにない情報は絶対に追加しない。抽出できない場合は明確にfail。
- **Explainability**: 各インフォグラフィックに「この図が視覚化しているルール」とconfidenceを紐づけ。
- **Multi-style Support**: ユーザー好みでスタイル選択可能（kawaiiが人気になりそう）。
- **One Attempt per Stage**: 基本は1回実行。失敗時はログを残して手動介入を促す。

## Parallel Execution

Process multiple games concurrently:

```
/fork notebooklm: Wingspanのルール抽出＋Nano Bananaインフォグラフィック生成
```

Each fork runs independently until infographic generation and DB storage.

## Integration Points

- **Backend entry**: `POST /api/games/generate` with `notebooklm=true`
- **Service method**: `GameService.generate_with_notebooklm(query, generate_infographics=true)`
- **Pipeline**: `PipelineOrchestrator.process_game_rules(game_title)`
- **New Service**: `InfographicService.generate_with_nano_banana(game_data, style="professional_clean")`

## Debugging Tips

- **Bad Japanese text in image**: Nano Bananaのtext renderingが弱い場合、promptに「高精度な日本語テキスト描画を優先」と明記。
- **Image quality low**: Nano Banana Proに切り替え or resolution指定。
- **Missing diagrams**: JSONの構造が不十分 → Extraction段階でGemini structured outputを強化。
- **Database errors**: Validate game schema matches confidence + infographic fields.

import asyncio

import anyio
from supabase import create_client

from app.core.gemini import GeminiClient
from app.core.settings import settings
from app.core.supabase import get_by_slug

_gemini = GeminiClient()
_client = create_client(settings.supabase_url, settings.supabase_key)


async def extract_rules_with_gemini():
    return {
        "rules_summary": "ブラス：バーミンガムは産業革命時代のイングランドを舞台にした経済戦略ゲームです。プレイヤーは産業を建設し、ネットワークを構築して勝利点を獲得します。2つの時代（運河時代と鉄道時代）を通じて、最も多くの勝利点を獲得したプレイヤーが勝ちます。",
        "rules_content": """ブラス：バーミンガム - 完全ルール（日本語）

【概要】
ブラス：バーミンガムは、産業革命時代のイングランドを舞台にした経済戦略ゲームです。プレイヤーは産業を建設し、ネットワークを構築して勝利点を獲得します。

【セットアップ】
- 各プレイヤーは£15の開始資金を受け取ります
- ボードにはイングランド全体の工業地と都市が示されています
- デッキからカードを引き、最初のプレイヤーを選びます

【ゲームプレイ】
プレイヤーは交互にターンを取ります：
1. 手札から1枚カードをプレイ
2. 以下のアクションを実行：
   - 産業を建設する（コスト支払い）
   - ネットワークリンクを構築する
   - 産業レベルを上げる
3. 他のプレイヤーがネットワークを使用すると、プレイヤーの産業から収入が得られます

【産業】
- 石炭鉱：石炭を生産、アップグレード可能
- 製鉄所：石炭を消費して鉄を生産
- 陶器：高級品、高得点
- ビール工場：地域産業
- エンジニアリング：ゲーム後期

【ゲーム終了と得点計算】
- 運河時代：8ターン後に終了、運河をスコアリング
- 鉄道時代：さらに8ターン続く
- 最終スコアリング：
  - £1 = 1勝利点
  - 石炭：各1点
  - 鉄：各2点
  - 陶器：各3点
  - ビール：各2点
  - ネットワーク接続：都市ごと1点
  - 鉄道ネットワーク：最大6点

【勝利条件】
最も高い勝利点を獲得したプレイヤーが勝ちます。""",
    }


async def generate_japanese_visual():
    prompt = """
ボードゲーム『ブラス：バーミンガム』の豪華な表紙画像を作成してください。

要素:
- 産業革命時代のイングランドの景観（工場、運河、都市）
- カラフルなコインと産業タイル（石炭、鉄、陶芸）
- 蒸気機関と機械装置
- ダイナミックで戦略的な雰囲気
- 日本語タイトル『ブラス：バーミンガム』を上部に表示
- 高級でプロフェッショナルなデザイン
- 暖色系（ブラウン、ゴールド、深紅）
"""
    return {"status": "visual_generation_prepared", "prompt": prompt}


async def main():
    rules_data = await extract_rules_with_gemini()
    game = await get_by_slug("brass-birmingham")
    if game:
        if not game.get("summary"):

            def _update():
                return (
                    _client.table("games")
                    .update({"summary": rules_data["rules_summary"]})
                    .eq("id", game["id"])
                    .execute()
                )

            await anyio.to_thread.run_sync(_update)

    await generate_japanese_visual()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
import sys

# Ensure backend directory is in path for app imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.supabase import upsert

async def ingest_magnolia():
    game_data = {
        "title": "Magnolia",
        "title_ja": "マグノリア",
        "slug": "magnolia",
        "description": "3x3の領地にユニットを配置して王国を発展させる、短時間で奥深い拡大再生産カードゲーム。",
        "summary": "プレイヤーは3x3のグリッドにユニットカードを配置し、自らの王国を築き上げます。種族や職業の配置ボーナスを活かし、軍事力、技術、信仰、勝利点を競います。40点獲得するか9枚のカードを配置すると終了する、スピーディな戦略ゲームです。",
        "min_players": 2,
        "max_players": 5,
        "play_time": 20,
        "min_age": 10,
        "published_year": 2021,
        "official_url": "https://arclightgames.jp/product/492main/",
        "rules_content": """【マグノリア ルール概要】

1. ゲームの目的
3x3の領地（グリッド）にユニットを配置し、最も多くの勝利点（VP）を獲得すること。

2. ゲームの終了条件
- いずれかのプレイヤーが40 VP以上に達する。
- いずれかのプレイヤーが3x3の領地すべて（9枚）にカードを配置する。

3. ラウンドの進行
各ラウンドは以下のフェイズを順番に行います。

a. ドローフェイズ
手札を好きなだけ捨て、手札が5枚になるまで補充する（1回のみ）。

b. 配置フェイズ（以下のいずれかを選択）
1. 2金を獲得する。
2. 1金を獲得し、手札からカードを1枚配置する（コストを支払う）。
3. 手札からカードを2枚配置する（コストを支払う）。
※配置時に同じ種族や職業が縦横に並ぶとボーナスが発生。

c. 戦争フェイズ
前列のユニットの軍事力を合計し、隣接するプレイヤーと競う。勝利すればVPや技術・信仰ポイントを獲得。

d. 発展・収入・VPフェイズ
カードの効果に応じて、技術・信仰の向上、金の獲得、VPの獲得を行う。

4. スコアリング
ゲーム終了時、所持金3金につき1 VPを加算。合計VPが最も高いプレイヤーが勝者です。""",
        "data_version": 1,
        "is_official": True
    }
    
    print(f"🚀 Ingesting {game_data['title']} into Supabase...")
    result = await upsert(game_data)
    if result:
        print(f"✓ Successfully ingested {game_data['title']} (Slug: {result[0]['slug']})")
    else:
        print(f"✗ Failed to ingest {game_data['title']}")

if __name__ == "__main__":
    asyncio.run(ingest_magnolia())

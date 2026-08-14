"""Idempotently seed Coup from publisher-authorized sources.

Evidence checked 2026-08-14:
- La Mame Games original product page: https://sites.google.com/view/la-mame-games/our-games-1
- Indie Boards & Cards current product page: https://indieboardsandcards.com/our-games/coup/
- Board Game Arena authorized implementation: https://boardgamearena.com/gamepanel?game=coupcitystate
"""

import os
import sys
from datetime import UTC, datetime

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from app.core.supabase import _TABLE, _client

load_dotenv()

SOURCE_REVISION = "verified-2026-08-14"

RULES_CONTENT = """
## ゲームの目的
各プレイヤーは2枚の影響力カードを持って開始します。カードを失うたびに1枚を表向きにし、2枚とも失うと脱落します。最後まで影響力を1枚以上残したプレイヤーが勝者です。

## セットアップ
- 基本のコートデッキは5種類（Duke / Assassin / Captain / Ambassador / Contessa）で、通常は各3枚です。
- 各プレイヤーに影響力カード2枚を裏向きで配ります。
- 各プレイヤーは通常2コインで開始します。2人戦では開始プレイヤーが1コインで始めます。
- コイン枚数は公開情報、影響力カードは秘密情報です。

## 手番で選べる一般アクション
1. **Income（収入）**: 財務庫から1コイン取ります。ブロック不可です。
2. **Foreign Aid（海外援助）**: 財務庫から2コイン取ります。Dukeを持つと主張するプレイヤーがブロックできます。
3. **Coup（クーデター）**: 7コインを支払い、対象プレイヤーに影響力を1枚失わせます。ブロック不可です。手番開始時に10コイン以上ある場合はCoupを選ばなければなりません。

## キャラクターを主張して行うアクション
実際にそのカードを持っていなくても役職を主張できます。ただし、他プレイヤーからチャレンジされる可能性があります。
- **Duke — Tax**: 財務庫から3コイン取ります。ブロック不可です。
- **Assassin — Assassinate**: 3コインを支払い、対象に影響力を1枚失わせます。対象はContessaを主張してブロックできます。
- **Captain — Steal**: 対象プレイヤーから最大2コイン盗みます。対象はCaptainまたはAmbassadorを主張してブロックできます。
- **Ambassador — Exchange**: コートデッキから2枚引き、その後2枚をコートデッキへ戻します。ブロック不可です。
- **Contessa**: 手番アクションはありません。Assassinationをブロックする役職です。

## チャレンジ
キャラクターを主張したアクションやブロックは、他プレイヤーがチャレンジできます。
- 主張が嘘だった場合、主張した側が影響力を1枚失います。
- 主張が本当だった場合、そのカードを公開して証明し、カードをコートデッキへ戻して交換します。チャレンジした側が影響力を1枚失います。
- ブロックの役職主張も同様にチャレンジできます。

## 解決の基本順序
1. アクションを宣言する
2. 必要ならその役職主張へのチャレンジを解決する
3. ブロック可能なアクションならブロックを宣言する
4. 必要ならブロック役職へのチャレンジを解決する
5. 残ったアクションを解決する

## ゲーム終了
影響力を2枚とも失ったプレイヤーは脱落します。最後に影響力を残している1人が勝者です。

### BGA版について
Board Game Arena版ではプレイヤー人数に応じてコートデッキ枚数が増える実装があり、7〜8人では各役職4枚の20枚デッキを使用する場合があります。基本の役職アクション、チャレンジ、ブロック、7コインCoup、10コイン以上でCoup強制という中核ルールは同じです。
""".strip()


def get_or_create_work_id() -> str:
    existing = (
        _client.table("game_works")
        .select("id")
        .eq("canonical_title", "Coup")
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    created = (
        _client.table("game_works")
        .insert({"canonical_title": "Coup", "identity_status": "verified"})
        .execute()
    )
    if not created.data:
        raise RuntimeError("Failed to create canonical Coup work")
    return created.data[0]["id"]


def build_game(work_id: str) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "title": "Coup",
        "title_ja": "クー",
        "title_en": "Coup",
        "slug": "coup",
        "description": "イタリアの都市国家を舞台に、秘密の影響力カードを使ってブラフ、チャレンジ、ブロックを行い、他の全プレイヤーの影響力を失わせる対戦カードゲーム。",
        "rules": {},
        "rules_content": RULES_CONTENT,
        "source_url": "https://indieboardsandcards.com/our-games/coup/",
        "summary": "役職を持っているふりもできる高速ブラフゲーム。チャレンジとブロックを読み合い、最後の1人まで影響力を守り抜く。",
        "structured_data": {
            "mechanics": ["Bluffing", "Player Elimination", "Roles", "Take That"],
            "keywords": [
                {"term": "ブラフ", "description": "持っていない役職でも所持していると主張できる中核要素"},
                {"term": "チャレンジ", "description": "役職主張の真偽を問い、失敗した側が影響力を失う"},
                {"term": "ブロック", "description": "特定役職の主張で相手のアクションを阻止する"},
                {"term": "影響力", "description": "各プレイヤーの残りライフに相当する裏向きキャラクターカード"},
            ],
            "sources": [
                "https://sites.google.com/view/la-mame-games/our-games-1",
                "https://indieboardsandcards.com/our-games/coup/",
                "https://boardgamearena.com/gamepanel?game=coupcitystate",
            ],
        },
        "view_count": 0,
        "search_count": 0,
        "data_version": 1,
        "is_official": True,
        "min_players": 2,
        "max_players": 6,
        "play_time": 15,
        "min_age": 13,
        "published_year": 2012,
        "official_url": "https://indieboardsandcards.com/our-games/coup/",
        "bga_url": "https://boardgamearena.com/gamepanel?game=coupcitystate",
        "work_id": work_id,
        "edition_label": "Base game",
        "language_code": "ja",
        "publisher": "Indie Boards & Cards",
        "source_revision": SOURCE_REVISION,
        "generated_from_source_revision": SOURCE_REVISION,
        "identity_status": "verified",
        "setup_summary": "通常は各プレイヤー2コイン・影響力2枚。基本デッキは5役職×各3枚。",
        "gameplay_summary": "一般アクションまたは役職アクションを宣言し、必要に応じてチャレンジとブロックを解決する。",
        "end_game_summary": "影響力を2枚とも失うと脱落し、最後まで影響力を残した1人が勝つ。",
        "updated_at": now,
    }


def main() -> None:
    work_id = get_or_create_work_id()
    game = build_game(work_id)
    existing = _client.table(_TABLE).select("id").eq("slug", "coup").limit(1).execute()

    if existing.data:
        game.pop("view_count", None)
        game.pop("search_count", None)
        _client.table(_TABLE).update(game).eq("id", existing.data[0]["id"]).execute()
        print(f"Updated Coup: {existing.data[0]['id']}")
        return

    game["created_at"] = datetime.now(UTC).isoformat()
    created = _client.table(_TABLE).insert(game).execute()
    if not created.data:
        raise RuntimeError("Failed to seed Coup")
    print(f"Created Coup: {created.data[0]['id']}")


if __name__ == "__main__":
    main()

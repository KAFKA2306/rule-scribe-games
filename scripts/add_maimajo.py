import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")

MAIMAJO_MD = """# 🧙‍♀️ マイマジョ (Mai Majo)

## 💎 ゲームの目的
お題に対する回答で「多数派（マジョリティ）」と「少数派（マイノリティ）」を見つけ出す正体隠匿パーティゲーム！

## 📦 コンポーネント
- 役職カード（マジョリティ、マイノリティ、インフルエンサー、ストーカー）
- 回答シート
- ペン

## 🚦 準備
1. プレイ人数に合わせて役職カードを準備。
2. 全員に1枚ずつ裏向きで配布、各自確認。

## 🔄 ゲームの流れ（1ゲーム5〜10分）

### フェイズ1: お題の公開
親が全員に共通のお題を提示。
例: 「おにぎりの具といえば？」「夏といえば？」

### フェイズ2: 回答の記入
役職に応じて回答を書く。

| 役職 | 回答の狙い |
|------|-----------|
| **マジョリティ** | 多くの人が書きそうな一般的な回答 |
| **マイノリティ** | 多数派に含まれない、でもズレすぎない回答 |
| **インフルエンサー** | マイノリティに見えるような目立つ回答 |
| **ストーカー** | マイノリティと同じ回答を狙う |

### フェイズ3: 回答の公開と議論
1. 全員の回答を一斉公開
2. 誰がマイノリティか3分程度議論
3. **即敗北**: マイノリティの回答が最多回答に含まれていたらマジョリティの勝ち

### フェイズ4: 投票
一斉に「マイノリティだと思う人」を指差し！

### フェイズ5: 勝敗判定
最多得票者が役職を公開。

## 🏆 勝利条件

| 役職 | 勝利条件 |
|------|---------|
| **マジョリティ** | 最多得票者がマイノリティ**ではない** |
| **マイノリティ** | 自分が最多得票 & 自分の回答が最多回答に含まれない |
| **インフルエンサー** | 自分が最多得票 |
| **ストーカー** | マイノリティと同じ回答 & マイノリティが最多得票 |

## 🛠 初心者向けヒント
- **マイノリティ**: 浮きすぎず埋もれすぎない絶妙な回答を狙え
- **マジョリティ**: 怪しい回答の人を議論で追い詰めろ
- **お題選び**: 回答がバラけやすいお題が面白い

## 📊 ゲーム情報
- **プレイ人数**: 5〜16人
- **プレイ時間**: 5〜10分
- **対象年齢**: 10歳以上
"""


def add_maimajo():
    game = {
        "title": "マイマジョ (Mai Majo)",
        "slug": "maimajo",
        "rules_content": MAIMAJO_MD,
        "description": "多数派vs少数派の正体隠匿パーティゲーム。お題への回答で心理戦！",
    }

    try:
        res = (
            supabase._client.table("games")
            .select("id")
            .eq("slug", game["slug"])
            .execute()
        )
        if res.data:
            print(f"⚠️ {game['slug']} already exists. Updating rules.")
            supabase._client.table("games").update({"rules_content": MAIMAJO_MD}).eq(
                "slug", game["slug"]
            ).execute()
        else:
            res = supabase._client.table("games").insert(game).execute()
            if res.data:
                print(f"✅ {game['slug']} added.")
            else:
                print(f"⚠️ {game['slug']}: Failed to add.")
    except Exception as e:
        print(f"❌ {game['slug']}: {e}")


if __name__ == "__main__":
    add_maimajo()

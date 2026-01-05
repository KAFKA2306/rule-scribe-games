import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")

TRICKY_SOUND_MD = """# 🎵 トリッキー・サウンド (Tricky Sound)

## 💎 ゲームの目的
手札のランクが分からない状態でトリックテイキング！推理と観察で獲得トリック数を正確に予想しよう。

## 📦 コンポーネント
- カードデッキ（複数スート、各ランク）
- スコアトラック

## 🚦 準備
1. カードをシャッフルして各プレイヤーに配布。
2. 各プレイヤーは配られたカードを**ランク順に裏向きで**自分の前に並べる。
3. カードの色と順番は分かるが、**実際のランク（数字）は不明**！

## 🔄 ゲームの流れ（全3ラウンド）

### トリックテイキングの基本ルール
| ルール | 内容 |
|--------|------|
| **切り札** | あり |
| **マストフォロー** | リードされたスートがあれば、そのスートを出す |

### ラウンドの進行
1. **カードをプレイ**: 順番にカードを1枚ずつ出す（裏向きから表に）
2. **トリック獲得**: 最も強いカードを出した人がトリックを獲得
3. **ビッド（任意）**: ラウンド途中で手札1枚を公開し、獲得トリック数を予想

### 💡 ビッドのポイント
- ラウンド中いつでも1枚を公開してビッド可能
- 公開したカードで自分のランクを推理しつつ、他人にも情報を与える駆け引き

## 🏆 得点計算
| 内容 | 点数 |
|------|------|
| 獲得トリック1つ | **1点** |
| ビッド的中 | **+5点** |

3ラウンドの合計点が最も高い人の勝ち！

## 🛠 初心者向けヒント
- **序盤は様子見**: 最初は他プレイヤーのカードを観察してランクを推理。
- **ビッドのタイミング**: 情報が集まってからビッドすると的中しやすい。
- **スートの管理**: マストフォローなので、手持ちスートの枚数を意識。

## 📊 ゲーム情報
- **プレイ人数**: 2〜5人
- **プレイ時間**: 約30分
- **対象年齢**: 12歳以上
- **原作**: Xylotar（シロタール）のリメイク
"""


def add_tricky_sound():
    game = {
        "title": "Tricky Sound (トリッキー・サウンド)",
        "slug": "tricky-sound",
        "rules_content": TRICKY_SOUND_MD,
        "description": "手札のランクが分からない状態で行うトリックテイキング。推理と駆け引きが熱い！",
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
            supabase._client.table("games").update(
                {"rules_content": TRICKY_SOUND_MD}
            ).eq("slug", game["slug"]).execute()
        else:
            res = supabase._client.table("games").insert(game).execute()
            if res.data:
                print(f"✅ {game['slug']} added.")
            else:
                print(f"⚠️ {game['slug']}: Failed to add.")
    except Exception as e:
        print(f"❌ {game['slug']}: {e}")


if __name__ == "__main__":
    add_tricky_sound()

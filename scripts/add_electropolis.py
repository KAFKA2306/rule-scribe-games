import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client.")

ELECTROPOLIS_MD = """# ⚡ 電力世界 (Electropolis)

## 💎 ゲームの目的
仮想都市の市長として、電力供給・環境汚染・市民支持のバランスを取りながら都市開発を進めよう！8ラウンドで最も高いスコアを獲得した人が勝者です。

## 📦 コンポーネント
- アクションボード
- プレイヤーボード（4枚）
- 建築タイル（144枚）
  - 発電所（石炭/ガス/原子力/太陽光/風力/水力）
  - 施設（博物館/病院/遊園地/公園/汚染防止施設など）
  - 燃料タイル（石炭/天然ガス/核燃料）
- 開発カード（32枚）
- トレンドカード（6枚）
- 市民支持度トラック、大気汚染指数トラック

## 🚦 準備
1. マップを選択し、ゲームボードを中央に配置。
2. プレイヤー数に応じてエリアを選択（隣接エリア推奨）。
3. 各プレイヤーにプレイヤーボードと初期リソースを配布。

## 🔄 ゲームの流れ（全8ラウンド）

### 各ラウンドの流れ
| フェイズ | 内容 |
|---------|------|
| **1. アクション選択** | アクションボードから建築タイル＋開発カードの組み合わせを選ぶ |
| **2. タイルの配置** | 開発カードで指定されたエリアにタイルを配置 |
| **3. 開発カード効果** | カード上部の特殊効果を適用（支持度獲得、ボーナス点など） |
| **4. 順位の調整** | 次ラウンドのプレイヤー順位を決定 |

### 💡 主要メカニクス

#### 発電所と公害
| 発電所タイプ | 特徴 |
|-------------|------|
| 石炭火力 | 高効率だが**大気汚染**を発生 |
| ガス火力 | 石炭より低汚染 |
| 原子力 | 安定供給だが**核廃棄物**問題 |
| 太陽光/風力/水力 | クリーンだが**供給不安定** |

#### 市民支持度
- 汚染が増えると支持度が低下
- 支持度が低いとゲーム進行に悪影響
- 公園や公共施設で支持度を回復

#### タイル配置ルール
- 既存タイルに**直交（上下左右）**または都市センターに隣接して配置
- 配置できないタイルは破棄→**支持度が減少**

#### 燃料管理
- 発電所によっては燃料タイル（石炭/ガス/核燃料）が必要
- 燃料はプレイヤーボード横に保管

## 🏆 勝利条件
8ラウンド終了後、以下を合計:
- 建築タイルの得点
- 開発カードの得点
- トレンドカードのボーナス
- 環境管理ボーナス

最高スコアの人が勝ち！

## 🛠 初心者向けヒント
- **汚染防止施設**: 火力発電を使うなら必須。早めに確保。
- **トレンドカードに注目**: ラウンドごとのボーナス条件を意識。
- **バランス重視**: 発電量だけでなく支持度も意識せよ。

## 📊 ゲーム情報
- **プレイ人数**: 2〜4人
- **プレイ時間**: 50〜70分
- **対象年齢**: 12歳以上
"""


def add_electropolis():
    game = {
        "title": "Electropolis (電力世界)",
        "slug": "electropolis",
        "rules_content": ELECTROPOLIS_MD,
        "description": "台湾発の都市建設ゲーム。電力供給と環境汚染のバランスを取りながら都市を発展させよう！",
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
                {"rules_content": ELECTROPOLIS_MD}
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
    add_electropolis()

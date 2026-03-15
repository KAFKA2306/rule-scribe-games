import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    print("Error importing supabase client. Making sure path is correct.")
ISTANBUL_DICE_MD = """
名作『イスタンブール』がダイスゲームになった！商人としてバザーを駆け巡り、サイコロの運と助手の力を借りて、誰よりも早くルビーを集めましょう。
- 特製ダイス 5個
- ゲームボード（人数によって裏表あり）
- 商品タイル、モスクタイル
- ルビー
自分の番には、以下の手順を行います。
1. **収入**: 自分の手元に「水晶」があれば、1つにつき1金を得る等の収入があります（アクションタイル効果）。
2. **ダイスロール**: ダイスを5個すべて振ります。
    - **振り直し**: 「水晶」を1つ支払うごとに、好きな数のダイスを選んで振り直せます（回数制限なし！）。
3. **アクション**: 出た目を使ってアクションを2回行います。
    - **商品獲得**: 同じ色の目×2 → その色の商品タイルをゲット。
    - **お金獲得**: 数字の合計値分のお金をゲット。
    - **カード**: カードの目 → ボーナスカードを引く。
    - **モスクタイル**: 特定の目を揃えて強力な効果を持つタイルを獲得。
    - **ルビー交換**: 商品やお金を支払ってルビーを獲得！（これが目的）
誰かが**ルビーを6個**（4人プレイなら5個）集めたら、そのラウンドを最後まで行ってゲーム終了。最も多くルビーを持っている人の勝利です。
- **モスクタイルは早めに**: これを持っていると「毎ターン収入」や「4個目のダイスとして使える」など強力な恩恵があります。序盤はルビーよりタイル優先が吉！
- **水晶は大事**: 欲しい目を出すには水晶による振り直しが不可欠です。常に1〜2個は持っておきましょう。
"""


def add_istanbul_dice():
    print("Adding Istanbul: The Dice Game...")
    new_game = {
        "title": "Istanbul: The Dice Game",
        "slug": "istanbul-dice-game",
        "rules_content": ISTANBUL_DICE_MD,
        "description": "イスタンブールのダイスゲーム版。サイコロを使って資源を集め、ルビーを獲得しよう！",
    }
    try:
        res = supabase._client.table("games").select("id").eq("slug", new_game["slug"]).execute()
        if res.data:
            print(f"⚠️ {new_game['slug']} already exists. Updating instead.")
            res = (
                supabase._client.table("games")
                .update({"rules_content": ISTANBUL_DICE_MD})
                .eq("slug", new_game["slug"])
                .execute()
            )
            print(f"✅ {new_game['slug']} updated.")
        else:
            res = supabase._client.table("games").insert(new_game).execute()
            if res.data:
                print(f"✅ {new_game['slug']} added successfully.")
            else:
                print(f"⚠️ Failed to add {new_game['slug']}: No data returned.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    add_istanbul_dice()

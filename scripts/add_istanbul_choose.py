import asyncio
import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError:
    pass

ISTANBUL_CHOOSE_MD = """# 📝 イスタンブール：選択と記録 (Istanbul: Choose & Write)

## 💎 ゲームの目的
「イスタンブール」の世界観をそのままに、紙とペンで遊ぶ「書いて遊ぶ」ゲームになりました！
プレイヤーは商人となり、カードを選んでリソースを集め、ルビーを誰よりも早く集めることを目指します。

## 📦 コンポーネント
- 個人シート（バザーマップ）
- 場所カード、ギルドカード
- 資源（商品、お金）の管理トラック

## 🔄 ゲームの流れ
自分の番には、以下の手順を行います。
1. **カードの選択**: 「場所カード」か「ギルドカード」を1枚選びます。
    - **場所カード**: 選んだカードのアクションを実行します（資源の獲得やルビーの交換など）。
    - **全プレイヤーアクション！**: 場所カードが選ばれた場合、**他のプレイヤーも同じアクションを実行できます！**（ただし、自分はアクションが強力になったり、他人は回数制限があったりします）。
    - **ギルドカード**: 強力なアクション！ただし、これは**自分だけ**が実行できます（他人は便乗不可）。
2. **シートへの記入**: アクションの結果、得た資源や商品を自分のシートにチェック（記録）します。
3. **ルビーの獲得**: 商品やお金を支払ってルビーのマスを埋めていきます。

## 🏆 勝利条件
誰かが規定数のルビー（例：10個前後、人数による）を集めたら、そのラウンドでゲーム終了。
- ルビーの数が最も多い人
- 同点なら残った資源などで決着

が勝利します。

## 🛠 初心者向けヒント
- **便乗を考えよう**: 自分の番でなくても、他人の選んだカードでアクションができます。「自分は何もしなくても商品がもらえる」タイミングを見逃さないように！
- **ギルドカードの使い所**: 他人に便乗させない「独り占めアクション」は強力です。差をつけたい時に使いましょう。
"""


def add_istanbul_choose():
    print("Adding Istanbul: Choose & Write...")

    new_game = {
        "title": "Istanbul: Choose & Write",
        "slug": "istanbul-choose-and-write",
        "rules_content": ISTANBUL_CHOOSE_MD,
        "description": "イスタンブールの紙ペンゲーム版（選択と記録）。カードを選んで全員でアクション！駆け引きが熱い！",
    }

    try:
        res = (
            supabase._client.table("games")
            .select("id")
            .eq("slug", new_game["slug"])
            .execute()
        )
        if res.data:
            print(f"⚠️ {new_game['slug']} already exists. Updating instead.")
            res = (
                supabase._client.table("games")
                .update({"rules_content": ISTANBUL_CHOOSE_MD})
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
    add_istanbul_choose()

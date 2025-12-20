import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.core.supabase import _TABLE, _client

load_dotenv()

# Manual Data
GAMES_DATA: List[Dict[str, Any]] = [
    {
        "title": "ボルカルス",
        "title_ja": "ボルカルス",
        "title_en": "Vulcanus",
        "summary": "富士から現れた怪獣対人間チームの非対称対戦ゲーム",
        "description": "怪獣プレイヤー1人対人間チーム1〜3人に分かれて戦う非対称対戦ゲームです。怪獣は東京の破壊を、人間は市民の避難と怪獣の撃退を目指します。",
        "rules_content": """
# ボルカルスの遊び方

## ゲームの概要
「怪獣」役のプレイヤー1人と、「人間」役のプレイヤー（1〜3人）に分かれて戦う、チーム対抗のボードゲームです。
怪獣は東京の街を破壊し尽くすことを目指し、人間チームは市民を守り、怪獣を倒すことを目指します。

## 勝利条件
- **怪獣の勝ち**: 東京を壊滅させる（被害トラックを進める）。
- **人間の勝ち**: 怪獣を撃退するか、市民を守り抜く。

## ゲームの流れ
全6ラウンド（予定）で進行します。

1. **計画フェイズ**:
   人間チームは作戦会議をして、アクションカードを伏せて出します。
   怪獣はそれを見て、自分のアクションカードを出します。
   *ポイント: 人間の作戦会議は怪獣にも聞こえています！*

2. **実行フェイズ**:
   出したカードを表にして、順番にアクションを実行します。
   怪獣が暴れたり、人間が消火活動や攻撃を行ったりします。

3. **イベントフェイズ**:
   ラウンドごとにイベントが発生し、状況が変化します。

## 初心者へのアドバイス
- **人間チームの方へ**: 完璧に守るのは難しいです。まずは市民の避難を優先しましょう！
- **怪獣の方へ**: 遠慮はいりません。思う存分、街を燃やしましょう！
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 80,
        "min_age": 10,
        "published_year": 2019,
        "official_url": "https://kaijuontheearth.com/vulcanus/",
        "image_url": None,  # Will be filled by other processes if needed, or null
        "is_official": True,
        "view_count": 0,
        "search_count": 0,
        "data_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "keywords": [
                {"term": "怪獣", "description": "プレイヤーの敵となる巨大生物"},
                {"term": "非対称", "description": "敵味方でルールや目的が違うこと"}
            ],
            "mechanics": ["Team-Based Game", "Variable Player Powers"]
        }
    },
    {
        "title": "ザ・クルー：第９惑星の探索",
        "title_ja": "ザ・クルー：第９惑星の探索",
        "title_en": "The Crew: The Quest for Planet Nine",
        "summary": "会話禁止の中でミッションに挑む協力型トリックテイキング",
        "description": "宇宙船の乗組員となり、第9惑星を目指す協力ゲームです。配られたミッション（特定のカードを取るなど）を全員で達成しなければなりません。ただし、相談は「通信トークン」を使った限定的な合図のみ。",
        "rules_content": """
# ザ・クルーの遊び方

## ゲームの概要
全員で協力してミッションをクリアしていくカードゲームです。
「トリックテイキング」というトランプのようなルールを使いますが、勝つことだけでなく「誰がどのカードを取るか」をコントロールする必要があります。

## 重要なルール：会話禁止
ゲーム中、「青の5持ってる？」や「あっちに出して！」といった会話は禁止です。
使えるのは、手札の情報を一部だけ伝える「通信トークン」のみ。

## ゲームの流れ
1. **ミッション確認**: 今回の目標（例：Aさんが緑の9を取る）を確認します。
2. **カードプレイ**: 順番にカードを1枚ずつ出します（マストフォロー：出された色と同じ色を持っていれば必ず出す）。
3. **トリックの勝敗**: 一番強いカードを出した人が、場のカードを総取りします。
4. **判定**: ミッション通りにカードを取れていれば成功！誰かが失敗したら即終了（やり直し）です。

## 初心者へのアドバイス
- 自分の手札だけでなく、仲間の手札を想像することが大切です。
- 失敗しても大丈夫。何度も挑戦してチームワークを高めましょう！
""",
        "min_players": 2,
        "max_players": 5,
        "play_time": 20,
        "min_age": 10,
        "published_year": 2019,
        "official_url": "https://www.gp-inc.jp/boardgame_the_crew.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Cooperative Game", "Trick-taking"]
        }
    },
    {
        "title": "たった今考えたプロポーズの言葉を君に捧ぐよ。 ：ラバーズピンク",
        "title_ja": "たった今考えたプロポーズの言葉を君に捧ぐよ。 ：ラバーズピンク",
        "title_en": "Instant Propose: Lover's Pink",
        "summary": "愛の言葉を叫ぶパーティゲームの甘々拡張セット",
        "description": "配られた単語カードを組み合わせて、制限時間内に最高のプロポーズを作るパーティゲームの拡張セットです。「ラバーズピンク」では、よりラブラブで甘い言葉や、少し重めの愛の言葉が追加されています。",
        "rules_content": """
# たった今考えたプロポーズの言葉を君に捧ぐよ。の遊び方

## ゲームの概要
親プレイヤー（指輪を渡される人）に向けて、他のプレイヤーが即興でプロポーズの言葉を作る大喜利パーティゲームです。
この「ラバーズピンク」セットには、甘い言葉た～っぷりのカードが入っています。

## ゲームの流れ
1. **カード配布**: 単語カードが配られます。
2. **プロポーズ作成**: 「結婚しよう」と言ってから、10秒カウントダウン！その間に手札のカードを並べ替えてプロポーズの台詞を作ります。
3. **プロポーズ**: 順番に、作った言葉を感情を込めて読み上げ、「結婚してください！」と指輪を差し出します。
4. **判定**: 親プレイヤーは、一番グッときたプロポーズの指輪を受け取ります。

## 初心者へのアドバイス
- 文法がおかしくても気にしない！勢いと愛情が大事です。
- 恥ずかしがらずに、なりきって演じると盛り上がります。
""",
        "min_players": 3,
        "max_players": 7,
        "play_time": 30,
        "min_age": 13,
        "published_year": 2019,
        "official_url": "https://clagla.jp/view/item/000000000002",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Party Game", "Word Game"]
        }
    },
    {
        "title": "おばけ屋敷の宝石ハンター：不気味な地下室（拡張）",
        "title_ja": "おばけ屋敷の宝石ハンター：不気味な地下室（拡張）",
        "title_en": "Ghost Fightin' Treasure Hunters: Creepy Cellar Expansion",
        "summary": "屋敷からの脱出ではなく、地下室へ宝石を運ぶ高難易度拡張",
        "description": "協力ゲーム『おばけ屋敷の宝石ハンター』の拡張セット。最強の敵「キングゴースト」が登場し、屋敷に閉じ込められたプレイヤーたちは、呪われた宝石を地下室へ運ばなければなりません。",
        "rules_content": """
# 不気味な地下室（拡張）の遊び方

## ゲームの概要
おばけ屋敷の宝石ハンターの拡張セットです。
基本ゲームとは逆に、屋敷内の宝石を集めて「地下室」へ運び込みます。
無敵の「キングゴースト」が徘徊し、難易度が大幅にアップ！

## 追加要素
- **地下室**: 宝石を運び込む目的地。
- **キングゴースト**: 絶対に倒せない最強のオバケ。彼がいると悪霊化が加速します。
- **呪われた宝石**: これを持って移動するのは大変です。

## ゲームの流れ
基本ルールは同じですが、目的が「脱出」から「地下室への搬入」に変わります。
1. **移動**: サイコロを振って移動。
2. **宝石運搬**: 屋敷中の呪われた宝石を拾い、地下室へ運びます。
3. **悪霊退治**: どんどん増えるオバケを協力して退治します。
4. **脱出**: 全ての宝石を運び終えたら、全員で脱出！

## 初心者へのアドバイス
- かなり難しいです！基本ゲームで慣れてから挑戦しましょう。
- キングゴーストからは逃げるしかありません。
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 45,
        "min_age": 8,
        "published_year": 2018,
        "official_url": "https://www.mattel.co.jp/toys/game_ghost_treasure_hunter_expansion.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Cooperative Game", "Dice Rolling"]
        }
    },
    {
        "title": "もっと私の世界の見方",
        "title_ja": "もっと私の世界の見方",
        "title_en": "Wie ich die Welt sehe... motto",
        "summary": "大喜利ゲーム「私の世界の見方」の追加お題・回答セット",
        "description": "大喜利パーティゲーム『私の世界の見方』の拡張セットです。単体では遊べません。新しいお題と単語カードが追加され、よりカオスで笑える組み合わせが楽しめます。",
        "rules_content": """
# もっと私の世界の見方の遊び方

## ゲームの概要
親が出した「お題カード（文章の穴埋め）」に対し、子が手札から一番面白いと思う「単語カード」を出して選んでもらう大喜利ゲームの拡張版です。

## ゲームの流れ
1. **お題発表**: 親がお題を読みます。「私の〇〇は世界一！」など。
2. **回答**: 子は手札から単語カードを裏向きで出します。
3. **選考**: 混ぜてからオープンし、親が一番気に入った回答を選びます。
4. **得点**: 選ばれた人が得点！

## 注意点
- これは拡張セットなので、基本セットが必要です。
- 変な単語でお腹が痛くなるほど笑えます。
""",
        "min_players": 2,
        "max_players": 9,
        "play_time": 30,
        "min_age": 10,
        "published_year": 2018,
        "official_url": "https://www.sugorokuya.jp/gamelist?n=wie_ich_die_welt_sehe_motto",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Party Game", "Voting"]
        }
    },
    {
        "title": "ボブジテンきっず",
        "title_ja": "ボブジテンきっず",
        "title_en": "Bob Jiten Kids",
        "summary": "カタカナ語禁止でお題を説明する子供向けボブジテン",
        "description": "「チョコレート」を「甘くて黒いお菓子」のように、カタカナ語を使わずに説明するゲームのキッズ版。お題が身近な言葉になり、子供でも遊びやすくなっています。",
        "rules_content": """
# ボブジテンきっずの遊び方

## ゲームの概要
日本語大好きな友人「ボブ」のために、カタカナ語を日本語だけで説明してあげるゲームです。

## ルール
1. **出題**: カードを引いて、お題（例：トマト）を決めます。
2. **説明**: 出題者は「カタカナ語」を使わずに説明します。「赤くて丸い野菜…」
   - 「レッド」とか「ベジタブル」と言ってはいけません！
3. **回答**: 分かった人は早押しで答えます。
4. **得点**: 正解したら出題者と回答者が1点ずつゲット。

## きっず版の特徴
- お題が子供にも分かりやすい言葉になっています。
- 特殊カード「エミリー」が出ると、色も言ってはいけなくなります！(トマトの説明で『赤』が禁止に！)
""",
        "min_players": 3,
        "max_players": 8,
        "play_time": 30,
        "min_age": 8,
        "published_year": 2018,
        "official_url": "https://bodoge.hoobby.net/games/bob-jiten-kids",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Party Game", "Communication"]
        }
    },
    {
        "title": "アズール：シントラのステンドグラス",
        "title_ja": "アズール：シントラのステンドグラス",
        "title_en": "Azul: Stained Glass of Sintra",
        "summary": "美しいステンドグラスを完成させるアズールシリーズ第2弾",
        "description": "タイル配置ゲーム『アズール』の続編。今回はステンドグラス職人となり、窓枠にガラス片をはめ込んでいきます。職人の移動やガラスの割れるリスクなど、無印アズールとは一味違う戦略が必要です。",
        "rules_content": """
# アズール：シントラのステンドグラスの遊び方

## ゲームの概要
工房からガラスタイルを取り、自分の窓枠ボードに配置して完成させるパズルゲームです。
見た目が非常に美しく、インスタ映え間違いなし！

## ゲームの流れ
1. **タイル獲得**: 工房（皿）から1色のタイルを全て取ります。残りは中央へ。
2. **配置**: 職人コマがいる列か、その右側の列にタイルを置きます。
3. **完成**: 縦一列が埋まると完成！得点が入ります。

## ポイント
- **職人の移動**: タイルを置くと職人はその列へ移動します。左に戻るには手番を1回パスする必要があります。
- **割れたガラス**: 置けなかったタイルはマイナス点になります。
- **美しさ**: 完成した時の達成感は格別です。
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 45,
        "min_age": 8,
        "published_year": 2018,
        "official_url": "https://hobbyjapan.games/azul_sgs/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Abstract Strategy", "Tile Placement"]
        }
    },
    {
        "title": "ソクラテスラ～キメラティック偉人バトル～",
        "title_ja": "ソクラテスラ～キメラティック偉人バトル～",
        "title_en": "Sokuratesura",
        "summary": "偉人のパーツを合体させて最強のキメラ偉人を作るバトルゲーム",
        "description": "「右腕」「胴体」「左腕」に分かれた偉人カードを組み合わせて、オリジナルの偉人を召喚！「ソクラテス」の右腕＋「ナポレオン」の胴体＋「信長」の左腕で最強の新偉人を作り出し、武力や知力でバトルします。",
        "rules_content": """
# ソクラテスラの遊び方

## ゲームの概要
偉人たちのパーツ（名前）を組み合わせて、変な名前の最強偉人を作って戦う大喜利バトルゲームです。
「ニコラス・ケイジ」のような名前いじりが楽しめます。

## ゲームの流れ
1. **召喚**: 手札から右腕・胴体・左腕を出して合体！「ソクラ・ペトラ・の父」みたいな偉人が爆誕。
2. **バトル**: 召喚した偉人で敵プレイヤーに攻撃！
3. **判定**: 武力や知力など、決まった能力値を比べて勝敗を決めます。

## クレイジーなポイント
- 名前が面白いと場が盛り上がります。
- 意外と真面目に能力バトルもしないといけません。
- 負けても笑えるのでパーティに最適です。
""",
        "min_players": 2,
        "max_players": 6,
        "play_time": 30,
        "min_age": 10,
        "published_year": 2018,
        "official_url": "https://azbstudio.tokyo/socratesla/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Party Game", "Hand Management"]
        }
    },
    {
        "title": "プラネット・メーカー",
        "title_ja": "プラネット・メーカー",
        "title_en": "Planet",
        "summary": "12面体の星に地形を作って動物を住まわせる立体パズル",
        "description": "専用の12面体コアに、磁石でくっつく地形タイルを貼って、自分だけの惑星を作るゲームです。地形がつながると、様々な動物たちが自分の星にやってきます。",
        "rules_content": """
# プラネット・メーカーの遊び方

## ゲームの概要
手元の立体惑星（12面体）に、砂漠や海などの地形タイルを貼り付けていく箱庭ゲームです。
見た目のインパクト大！

## ゲームの流れ
1. **タイル選択**: 場にある5枚のタイルから順に1枚選びます。
2. **配置**: 自分の惑星の好きな場所にペタッと貼ります（磁石です）。
3. **動物判定**: 3ターン目以降、特定の地形（例：海またぎの氷原）を一番多く持っている人の星に、動物カードがやってきます。
4. **得点**: ゲーム終了時、動物カードの点数と、秘密の目標カードの点数を合計して競います。

## ポイント
- 立体なので、裏側の地形も把握しながらパズルをする必要があります。
- 動物を集めるのが楽しい！
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 30,
        "min_age": 8,
        "published_year": 2018,
        "official_url": "https://arclightgames.jp/product/planet/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Pattern Building", "Drafting"]
        }
    },
    {
        "title": "タイムライン：博識編",
        "title_ja": "タイムライン：博識編",
        "title_en": "Timeline: Classic",
        "summary": "歴史の出来事を年代順に並べる雑学カードゲーム",
        "description": "「紅茶の発明」「ハリーポッターの出版」「電球の発明」…これらを年代順に並べられますか？自分の手札のカードを、場のタイムライン（年表）の正しい位置に差し込んでいくクイズゲームです。",
        "rules_content": """
# タイムライン：博識編の遊び方

## ゲームの概要
様々な出来事が書かれたカードを、正しい年代順に並べていくゲームです。
正確な年号を知らなくても、「これはピラミッドよりは後だろう…」といった推測で戦えます。

## ゲームの流れ
1. **手札**: 全員に数枚のカードが配られます（年代は見えません）。
2. **配置**: 手番の人は、自分のカードを場の年表の「どこに入るか」予想して置きます。
3. **答え合わせ**: カードを裏返して年代を確認！
   - **正解**: そのまま置かれます。手札が減って嬉しい！
   - **不正解**: カードは捨てられ、山札から1枚引かされます（手札減らず）。
4. **勝利**: 最初に手札を無くした人の勝ち！

## ポイント
- 博識編は、歴史、発明、文化などジャンルが多彩です。
- 意外な事実（缶切りの発明は缶詰のずっと後！？）に盛り上がります。
""",
        "min_players": 2,
        "max_players": 6,
        "play_time": 15,
        "min_age": 8,
        "published_year": 2018,
        "official_url": "https://hobbyjapan.games/timeline/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Trivia", "Card Game"]
        }
    },
    {
        "title": "ボブジテン",
        "title_ja": "ボブジテン",
        "title_en": "Bob Jiten",
        "summary": "カタカナ語を日本語だけで説明する『ボブジテン』シリーズ第一弾",
        "description": "「インターネット」を「世界規模の電脳網」のように、外来語（カタカナ語）を一切使わずに説明するパーティゲーム。「きっず」版よりもお題が少し大人向けです。",
        "rules_content": """
# ボブジテンの遊び方

## ゲームの概要
カタカナ語（外来語）を、カタカナ語を使わず日本語だけで説明するコミュニケーションゲームです。

## ゲームの流れ
1. **お題決定**: カードを引いてお題を決めます（例：オーケストラ）。
2. **説明**: 出題者は日本語だけで説明します。「大勢で演奏する楽団…」
   - 「バイオリン」や「コンサート」といったカタカナ語はNG！
3. **回答**: 分かった人は答えます。早い者勝ち。
4. **得点**: 正解者と出題者に1点。

## ポイント
- うっかりカタカナ語を言ってしまうと、指摘されてお手つきになります。
- 「トニー」が出たらカタカナ語禁止＋「てにおは」禁止！片言で説明しないといけません。
""",
        "min_players": 3,
        "max_players": 8,
        "play_time": 30,
        "min_age": 10,
        "published_year": 2017,
        "official_url": "https://bodoge.hoobby.net/games/bob-jiten",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Party Game", "Communication"]
        }
    },
    {
        "title": "キャッチ・ザ・ムーン",
        "title_ja": "キャッチ・ザ・ムーン",
        "title_en": "Catch the Moon",
        "summary": "雲の上にハシゴを積み上げて月を目指す美しいバランスゲーム",
        "description": "雲の土台の上に、ハシゴを互い違いに組んで高く積み上げていくバランスゲームです。サイコロの指示に従って、「ハシゴ1本だけに接する」などの条件を守りながら積んでいきます。崩したら「月の涙」を受け取ってしまいます。",
        "rules_content": """
# キャッチ・ザ・ムーンの遊び方

## ゲームの概要
ハシゴを崩さないように積み上げていく、ジェンガのようなドキドキ感のあるバランスゲームです。
見た目がとても幻想的で美しいのが特徴。

## ゲームの流れ
1. **ダイス**: サイコロを振って、積み方の指示を見ます。
   - 「ハシゴ1本だけに触れるように置く」
   - 「ハシゴ2本に触れるように置く」
   - 「一番高い位置になるように置く」
2. **配置**: 指示通りにハシゴを置きます。
3. **判定**:
   - 成功なら次の人へ。
   - 崩してしまったらペナルティ（月の涙）。
   - 土台やテーブルに触れてしまってもペナルティ。

## 勝利条件
- 誰かが「月の涙」を全て受け取るか、ハシゴが無くなるまで続けます。
- 「月の涙」が一番少ない人が勝ち！
""",
        "min_players": 2,
        "max_players": 6,
        "play_time": 20,
        "min_age": 6,
        "published_year": 2017,
        "official_url": "https://hobbyjapan.games/catch_the_moon/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Dexterity", "Stacking"]
        }
    },
    {
        "title": "テストプレイなんてしてないよ",
        "title_ja": "テストプレイなんてしてないよ",
        "title_en": "We Didn't Playtest This at All",
        "summary": "「勝利する」と書かれたカードを出せば勝てる理不尽なバカゲー",
        "description": "アメリカ発の混沌としたパーティゲーム。カードには「このカードを出せば勝利する」「身長が低い人は敗北する」など、無茶苦茶な効果が書かれています。1分で終わることもあれば、誰も勝てないことも。",
        "rules_content": """
# テストプレイなんてしてないよの遊び方

## ゲームの概要
タイトル通り、バランス調整なんてされていない（ような）、何が起こるか分からない理不尽カードゲームです。
目的は「勝利すること」。

## ゲームの流れ
1. **ドロー**: 山札から1枚引きます。
2. **プレイ**: 手札から1枚出します。
3. **効果解決**: カードの指示に従います。
   - 「あなたは勝利する」→ その時点で勝ち！ゲーム終了。
   - 「〇〇な人は敗北する」→ 条件に当てはまる人は脱落。

## よくある展開
- ジャンケンで負けて即敗北。
- 全員同時に敗北して勝者なし。
- 30秒で決着。

## 楽しみ方
- 真面目に戦略を練ってはいけません。
- 理不尽な死に様を笑い飛ばしましょう！
""",
        "min_players": 2,
        "max_players": 10,
        "play_time": 5,
        "min_age": 13,
        "published_year": 2017,
        "official_url": "http://www.groupsne.co.jp/products/bg/testplay/testplay.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Party Game", "Player Elimination"]
        }
    },
    {
        "title": "ダンジョンオブマンダム：エイト",
        "title_ja": "ダンジョンオブマンダム：エイト",
        "title_en": "Dungeon of Mandom VIII",
        "summary": "裸一貫でダンジョンに挑むか、装備を捨ててチキンレースするか",
        "description": "「俺はこんな装備なくても勝てるぜ？」と虚勢を張り合うチキンレース・ブラフゲーム。装備を捨てながらモンスターをダンジョンに送り込み、最後に誰もパスしなかった一人が、残った貧弱な装備でダンジョン踏破に挑みます。",
        "rules_content": """
# ダンジョンオブマンダム：エイトの遊び方

## ゲームの概要
RPGの世界観で行う、度胸試しとハッタリのゲームです。
冒険者は1人だけ。みんなで「俺ならもっと軽装備で行ける」と競い合い、誰かが挑むことになります。

## ゲームの流れ
1. **アクション**: 山札からカードを引きます。
   - **モンスターを配置**: ダンジョン（裏向きの山）に加えます。
   - **装備を捨てる**: モンスターを手元に隠し持ち、代わりに冒険者の装備を1つ外します（弱体化）。
2. **パス**: 「これ以上は無理だ」と思ったらパス。降ります。
3. **挑戦**: 最後までパスしなかった1人が、残った装備でダンジョンに挑みます。
4. **判定**:
   - 装備の効果で、めくられたモンスターを倒せればクリア！
   - 死んだら失敗。

## 勝利条件
- 2回クリアするか、他の全員を脱落させれば勝ち。

## ポイント
- 強いモンスターをこっそり入れておいて、他人に挑ませる罠を仕掛けるのが楽しい！
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 30,
        "min_age": 10,
        "published_year": 2017,
        "official_url": "https://oinkgames.com/ja/games/analog/dungeon-of-mandom-viii/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Bluffing", "Push Your Luck"]
        }
    },
    {
        "title": "ゲスクラブ",
        "title_ja": "ゲスクラブ",
        "title_en": "Guess Club",
        "summary": "みんなの回答を予想して賭ける「推測」パーティゲーム",
        "description": "「学校にあるものといえば？」のようなお題に対して、全員で6つの回答を書きます。その後、「チョークと書いた人は何人いるか？」を推測して賭けを行います。感性がズレていると全く当たりません！",
        "rules_content": """
# ゲスクラブの遊び方

## ゲームの概要
「みんなが書きそうなこと」を書いて、それがどれくらい被るかを予想するゲームです。
連想ゲームと賭け要素が合体しました。

## ゲームの流れ
1. **回答**: お題（例：赤い食べ物）について、6つの答えを書きます。
2. **プレイ**: 1人が自分の答えを1つ出します。（例：「リンゴ」）
3. **確認**: 他の人も「リンゴ」を書いていたら出します。
4. **賞金**: 書いていた人数によって賞金をゲット！
5. **賭け**: 自分の番以外でも、「このラウンドで『3人被り』は何回起こるか？」などを予想して賭けられます。

## ポイント
- あえてマイナーな答えを書くか、ベタな答えで攻めるか？
- 「えっ、それを書かないの！？」という驚きが盛り上がります。
""",
        "min_players": 2,
        "max_players": 8,
        "play_time": 30,
        "min_age": 10,
        "published_year": 2017,
        "official_url": "http://www.cosaic.co.jp/games/guess_club.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Party Game", "Betting"]
        }
    },
    {
        "title": "フォントかるた",
        "title_ja": "フォントかるた",
        "title_en": "Font Karuta",
        "summary": "フォントの形だけで札を取る、デザイナー泣かせ＆歓喜のかるた",
        "description": "取り札には全部「愛のあるユニークで豊かな書体。」と書いてあります。違うのはフォント（書体）だけ！読み手が「ゴシックMB101 B！」と読んだら、そのフォントの札を取ります。",
        "rules_content": """
# フォントかるたの遊び方

## ゲームの概要
絶対フォント感（？）が試される異色のかるたです。
文字の内容は全部同じ。線の太さや形（ハネ、ハライ）だけで判断します。

## ゲームの流れ
1. **準備**: 札を広げます。
2. **詠み上げ**: 「リュウミン B-KL！」のようにフォント名と解説が読まれます。
3. **取り**: 正しいフォントの札を取ります。
4. **確認**: 札の裏に正解が書いてあります。

## 初心者へのアドバイス
- 最初は全く見分けがつきませんが、解説を聞くと「なるほど！」となります。
- 「明朝体」と「ゴシック体」の違いから始めましょう。
- デザイナーと遊ぶとボコボコにされるかもしれません。
""",
        "min_players": 1,
        "max_players": 10,
        "play_time": 15,
        "min_age": 10,
        "published_year": 2017,
        "official_url": "https://www.fontkaruta.com/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Pattern Recognition", "Memory"]
        }
    },
    {
        "title": "狂気山脈",
        "title_ja": "狂気山脈",
        "title_en": "Mountains of Madness",
        "summary": "クトゥルフ神話をテーマにした、狂気が伝染する協力ゲーム",
        "description": "南極探検隊となって、狂気の山脈からの脱出を目指します。しかし、恐怖によりプレイヤーはどんどんおかしくなっていきます。「単語でしか喋れない」「誰かと手をつなぐ」などの狂気カードが、真面目な相談を阻害します。",
        "rules_content": """
# 狂気山脈の遊び方

## ゲームの概要
協力してミッション（カード出し）をクリアしていくゲームですが、プレイヤーはおかしく（狂気状態に）なります。
真剣にクリアしたいのに、変な行動をしてしまうジレンマを楽しむパーティ寄り協力ゲームです。

## ゲームの流れ
1. **移動**: 山脈を進みます。
2. **遭遇**: タイルをめくって試練を確認（例：道具と本で合計15にする）。
3. **相談**: 制限時間30秒で、誰が何を出すか相談します。
   - **狂気**: 「質問には質問で返す」などの狂気カードを持っている人は、それに従わないといけません。
4. **解決**: 成功すれば報酬、失敗すればペナルティ＆狂気が悪化。

## ポイント
- 狂気プレイが面白いので、失敗しても笑えます。
- ちゃんとクリアするのは結構難しいです！
""",
        "min_players": 3,
        "max_players": 5,
        "play_time": 60,
        "min_age": 12,
        "published_year": 2017,
        "official_url": "https://hobbyjapan.games/mountains_of_madness/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Cooperative Game", "Communication Limits"]
        }
    },
    {
        "title": "新・キング・オブ・トーキョー",
        "title_ja": "新・キング・オブ・トーキョー",
        "title_en": "King of Tokyo: Renewal",
        "summary": "怪獣王になって東京を破壊し尽くすダイスバトルゲーム",
        "description": "巨大怪獣になって東京で大暴れ！サイコロを振って敵を殴ったり、エネルギーを溜めて進化したりします。最後まで立っていた怪獣か、勝利点を集めきった怪獣が勝者です。",
        "rules_content": """
# 新・キング・オブ・トーキョーの遊び方

## ゲームの概要
怪獣映画の主役になって殴り合う、爽快な対戦ダイスゲームです。
ルールはシンプルで攻撃的！

## ゲームの流れ
1. **ダイス**: サイコロを6個振ります（振り直し2回OK）。
2. **効果解決**:
   - **攻撃（爪）**: 他の怪獣にダメージ！東京の中にいると、外の全員を攻撃。外にいると中の怪獣を攻撃。
   - **回復（ハート）**: 体力を回復（東京の中では回復不可！）。
   - **エネルギー（雷）**: エネルギーをゲットして「パワーカード（特殊能力）」を買う。
   - **点数（数字）**: そろえる勝利点ゲット。
3. **移動**: 誰もいなければ東京に入れます。東京にいると毎ターン点数が入りますが、全員から殴られます。

## 勝利条件
- 20点集める。
- または、自分以外の全員を倒す。

## ポイント
- いつ東京に入って、いつ逃げるかの駆け引きが熱い！
- パワーカードで「頭が生える」などの進化をするのも楽しいです。
""",
        "min_players": 2,
        "max_players": 6,
        "play_time": 30,
        "min_age": 8,
        "published_year": 2016,
        "official_url": "https://hobbyjapan.games/king_of_tokyo_new_edition/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Dice Rolling", "King of the Hill"]
        }
    },
    {
        "title": "クイズいいセン行きまSHOW！恋愛編",
        "title_ja": "クイズいいセン行きまSHOW！恋愛編",
        "title_en": "Quiz Iisen ikimaSHOW! Rennai-hen",
        "summary": "恋愛観の「ちょうど真ん中」を目指す価値観共有クイズゲーム",
        "description": "「付き合う前のデートは月何回が理想？」などの正解のない問いに対し、全員で数字で答えます。その場のみんなの答えの「中央値」を書いた人が正解！恋愛観の違いが浮き彫りになって盛り上がります。",
        "rules_content": """
# クイズいいセン行きまSHOW！恋愛編の遊び方

## ゲームの概要
正解のないクイズに対して、みんなの回答の「真ん中」を当てるゲームです。
恋愛編なので、お題はすべて恋愛関連！

## ゲームの流れ
1. **出題**: 「彼氏・彼女の浮気、どこから許せない？（1.手をつなぐ～10.旅行）」のような問題を読みます。
2. **回答**: 全員がボードに数字を書きます。
3. **公開**: 一斉にオープン！
4. **判定**: 数字を小さい順に並べて、ちょうど真ん中の人が「正解」！

## ポイント
- 自分の価値観ではなく、「みんなならこう書くだろう」という平均を予想するのがコツ。
- 同じ数字を書いた二人は「ラブ状態」としてポイントを貰えます。
""",
        "min_players": 3,
        "max_players": 10,
        "play_time": 20,
        "min_age": 8,
        "published_year": 2017,
        "official_url": "https://arclightgames.jp/product/%E3%82%AF%E3%82%A4%E3%82%BA%E3%81%84%E3%81%84%E3%82%BB%E3%83%B3%E8%A1%8C%E3%81%8D%E3%81%BEshow%EF%BC%81-%E6%81%8B%E6%84%9B%E7%B7%A8/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Voting", "Party Game"]
        }
    },
    {
        "title": "ギャンブラー×ギャンブル！",
        "title_ja": "ギャンブラー×ギャンブル！",
        "title_en": "Gambler x Gamble!",
        "summary": "カジノを舞台に、運とハッタリで富豪を目指すカード＆ダイスゲーム",
        "description": "悪名高いカジノへギャンブラーを送り込みます。「運命カード」の数値と自分のギャンブラーの条件が合えば大金ゲット。しかし、他プレイヤーの出し方も計算に入れないと、一文無しに…？",
        "rules_content": """
# ギャンブラー×ギャンブル！の遊び方

## ゲームの概要
ブラフ（はったり）と運の要素が絡む対戦カードゲームです。
自分の持っている数字に合うように、場の合計値を操作します。

## ゲームの流れ
1. **カード選択**: 手札から「0」か「1」のカードを伏せて出します。
2. **公開**: 全員が出したカードをオープン。合計値を計算します。
3. **判定**: 自分の手元の「ギャンブラーカード（例：合計が2なら当たり）」と照らし合わせます。
   - 当たれば報酬ゲット！
   - 特殊なカードで合計値を＋－操作もできます。

## 勝利条件
- 15金稼ぐ。
- または「4」や「8」などの大穴を一発当てる。

## ポイント
- 「あいつは0を出してくるはず…だから自分は1だ！」という読み合いが熱いです。
""",
        "min_players": 3,
        "max_players": 4,
        "play_time": 20,
        "min_age": 10,
        "published_year": 2016,
        "official_url": "http://www.groupsne.co.jp/products/bg/gambler/gambler.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Bluffing", "Betting"]
        }
    },
    {
        "title": "狩歌 基本セット",
        "title_ja": "狩歌 基本セット",
        "title_en": "CARU UTA Basic Set",
        "summary": "J-POPなどの好きな曲を流して遊ぶ、新感覚かるた",
        "description": "「君」「未来」「愛」など、J-POPによく出てくる単語がカードになっています。好きな曲を流して、歌詞に出てきた単語のカードを素早く取ります。カラオケでも遊べます！",
        "rules_content": """
# 狩歌（かるうた）の遊び方

## ゲームの概要
「曲を流しながらかるたをする」ゲームです。
読み手はいません。アーティストが読み手です。

## ゲームの流れ
1. **準備**: カードを広げます。
2. **選曲**: 好きな曲（日本語の歌）を流します。
3. **プレイ**: 歌詞を聞き取ります。「♪～君が好き～」と流れたら、「君」と「好き」のカードを探して取ります！
4. **得点**: カードに書かれた点数を合計します。「愛」などはよく出るので点数が低いかも？

## ポイント
- 知っている曲だと有利ですが、歌詞カードを見ながら知らない曲でやっても面白いです。
- プレイリストを作って遊ぶのがおすすめ。
""",
        "min_players": 2,
        "max_players": 8,
        "play_time": 10,
        "min_age": 6,
        "published_year": 2016,
        "official_url": "https://www.xaquinel.com/games/caruuta/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Pattern Recognition", "Music"]
        }
    },
    {
        "title": "バウンス・オフ！",
        "title_ja": "バウンス・オフ！",
        "title_en": "Bounce-Off",
        "summary": "ピンポン玉をワンバウンドさせて入れる、アクション・テーブルゲーム",
        "description": "指令カード通りの形になるように、トレーにピンポン玉を投げ入れます。ただし、必ず「ワンバウンド」以上させないといけません。シンプルながら技術と集中力が必要なアクションゲームです。",
        "rules_content": """
# バウンス・オフ！の遊び方

## ゲームの概要
ピンポン玉を投げて、並べる。それだけですが意外と入りません！
体を使うアクションゲームです。

## ゲームの流れ
1. **指令**: カードを引いて、作る形（例：Xの形）を決めます。
2. **アクション**: 自分の色のボールを投げます。
   - **ルール**: 必ずテーブルで1回以上バウンドさせてからトレーに入れること。
3. **交代**: 交互に投げるか、または一斉に投げまくる（カオスモード）か選べます。
4. **勝利**: 最初に形を完成させた人がカードゲット。3枚取ったら勝ち。

## ポイント
- 力加減が全てです。
- 相手の邪魔をする場所にわざと入れるのも戦略です。
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 15,
        "min_age": 7,
        "published_year": 2014,
        "official_url": "https://mattel.co.jp/toys/mattel_games/bounce_off.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Dexterity", "Pattern Building"]
        }
    },
    {
        "title": "パンデミック：クトゥルフの呼び声",
        "title_ja": "パンデミック：クトゥルフの呼び声",
        "title_en": "Pandemic: Reign of Cthulhu",
        "summary": "協力ゲームの金字塔×クトゥルフ神話。狂気に抗い世界を救え",
        "description": "世界を救う協力ゲーム「パンデミック」のシステムで、クトゥルフ神話の邪神復活を阻止します。ウイルスではなく「信徒」や「ショゴス」が増殖。解決しようとすると正気度（SAN値）が減り、発狂してしまうリスクと戦います。",
        "rules_content": """
# パンデミック：クトゥルフの呼び声の遊び方

## ゲームの概要
全員で協力して、世界中に現れるゲートを封印するゲームです。
失敗条件が多く、難易度は歯ごたえがあります。

## ゲームの流れ
1. **アクション**: 移動したり、邪教の信徒（敵）を撃退したり、カードを交換したりします。
2. **カード補充**: 手札を補充しますが、「邪悪の胎動」カードが出ると敵が急増します。
3. **感染（召喚）**: 新たな場所に信徒が現れます。

## 特殊ルール：正気度（SAN値）
- 恐ろしい敵（ショゴス）と同じ場所にいたり、ゲートを通ったりするとダイスを振ります。
- 正気度がなくなると「発狂」し、行動制限などのデメリットを受けます。
- 全員が発狂すると敗北！

## 勝利条件
- 4つのゲートを全て封印する。

## ポイント
- 通常のパンデミックよりマップが狭いですが、敵の処理に追われます。
- 正気度管理が非常に重要です。
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 40,
        "min_age": 14,
        "published_year": 2016,
        "official_url": "https://hobbyjapan.games/pandemic_cthulhu/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Cooperative Game", "Action Points"]
        }
    },
    {
        "title": "キングドミノ",
        "title_ja": "キングドミノ",
        "title_en": "Kingdomino",
        "summary": "タイルを繋げて自分だけの王国を作る、ドイツ年間ゲーム大賞受賞作",
        "description": "5×5マスの王国を作り上げるパズル＆ドラフトゲームです。「森」や「海」などのタイルをうまく繋げて、高得点を目指します。ルールは簡単ですが、どのタイルを優先して取るかの駆け引きが熱いです。",
        "rules_content": """
# キングドミノの遊び方

## ゲームの概要
タイルを並べて自分だけの王国を作るゲームです。
ドミノのように、同じ地形を繋げて並べていきます。

## ゲームの流れ
1. **タイルの選択**: 4つのタイルから欲しいものに自分のコマを置きます。
   - **ポイント**: 良いタイル（王冠付きなど）は番号が大きく、取ると次回の順番が遅くなります。
2. **配置**: 自分の王国にタイルを配置します。
   - **ルール**: 「同じ地形同士が最低1辺接していること」。スタート地点（お城）は何でも繋がります。
   - 5×5マスの枠からはみ出さないように注意！
3. **繰り返し**: すべてのタイルがなくなるまで繰り返します。

## 勝利条件
- 「繋がった地形のマス数」×「その中にある王冠の数」が得点になります。
- 合計点が一番高い人の勝ち！

## 初心者へのアドバイス
- どんなに広げても、「王冠」がないと0点です！王冠付きタイルを確保しましょう。
- 5×5の中心にお城が来るように作るとボーナス点がある場合も（ヴァリアントルール）。
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 15,
        "min_age": 8,
        "published_year": 2016,
        "official_url": "https://ten Days Games", 
        "is_official": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Tile Placement", "Drafting"]
        }
    },
    {
        "title": "ロクジカ",
        "title_ja": "ロクジカ",
        "title_en": "Lokgica",
        "summary": "1次×2次×3次産業＝6次産業化！地域おこしカードゲーム",
        "description": "「生産」「加工」「販売」の3つのカードを揃えて、六次産業化プロジェクトを完成させます。地味なテーマに見えますが、コンボを決める爽快感と、地域を活性化させる達成感が味わえる隠れた名作です。",
        "rules_content": """
# ロクジカの遊び方

## ゲームの概要
あなたは地域おこしのプロデューサー。
素材（1次）・加工（2次）・販売（3次）を組み合わせて、商品開発を成功させましょう！

## ゲームの流れ
1. **カード獲得**: 場から素材カードなどを獲得します。
2. **プロジェクト完成**: 手札から「1次」「2次」「3次」のカードを1枚ずつ出してセットにします。
   - 例：【トマト】×【ケチャップ加工】×【ネット通販】
3. **収入**: 完成したプロジェクトの点数分、お金が入ります。そのお金でさらに強いカードを買えます。

## 勝利条件
- 稼いだお金や、プロジェクト点数を合計して競います。

## ポイント
- 組み合わせによってはボーナスが発生します。
- 「6次産業化」という実際のビジネス用語が学べる社会派ゲームでもあります。
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 30,
        "min_age": 8,
        "published_year": 2015,
        "official_url": "https://gamemarket.jp/game/13357",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Set Collection", "Card Drafting"]
        }
    },
    {
        "title": "ナンジャモンジャ・ミドリ",
        "title_ja": "ナンジャモンジャ・ミドリ",
        "title_en": "Toddles-Bobbles Green",
        "summary": "変な生き物に名前をつけて、再登場したら叫ぶ！爆笑ネーミングゲーム",
        "description": "謎の生物「ナンジャモンジャ」のカードをめくり、初めて出た顔なら名前をつけます。「田中」「もじゃもじゃ」「昨日食べた夕飯」なんでもOK。もし既に名前がついているやつが出たら、その名前をいち早く叫んだ人がカードをゲット！",
        "rules_content": """
# ナンジャモンジャ・ミドリの遊び方

## ゲームの概要
記憶力と瞬発力の勝負！自分たちで変な名前をつけるのが一番の面白ポイントです。
シロ版とミドリ版がありますが、絵柄が違うだけです。混ぜても遊べます。

## ゲームの流れ
1. **めくる**: 山札からカードを1枚めくります。
2. **ネーミング**: 初めて見る生物なら、好きな名前をつけます。「ジェニファー」とか「足長おじさん」とか。
3. **叫ぶ**: 既に名前がついている生物なら、その名前を叫びます！
   - 一番早かった人が、溜まっているカードを全部もらえます。

## 勝利条件
- 山札がなくなったとき、一番カードを持っている人の勝ち。

## 初心者へのアドバイス
- 短い名前（例：ポチ）は呼びやすいですが、長い名前（例：南の島の魔法使いポポ）をつけると、みんなが噛んで面白いことになります。
""",
        "min_players": 2,
        "max_players": 6,
        "play_time": 15,
        "min_age": 4,
        "published_year": 2010,
        "official_url": "https://sugorokuya.jp/p/nanjamonja",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Memory", "Pattern Recognition"]
        }
    },
    {
        "title": "キョンシー",
        "title_ja": "キョンシー",
        "title_en": "GANGSI",
        "summary": "磁石でカチッと捕まる！キョンシーvsトレジャーハンターの恐怖の鬼ごっこ",
        "description": "ついたてを挟んで、見えないキョンシーから逃げながらお宝を集めるハンターと、音と勘を頼りにハンターを追い詰めるキョンシーの非対称対戦ゲーム。同じマスに入ると磁石でコマがくっつくギミックが秀逸です。",
        "rules_content": """
# キョンシー（GANGSI）の遊び方

## ゲームの概要
ボードを立てて向かい合い、相手が見えない状態で動く「ステルス」鬼ごっこです。
キョンシー役（1人）VS ハンター役（その他）で分かれます。

## ゲームの流れ
1. **ハンターの手番**: ダイスを振って移動し、お宝を集めます。
   - お宝を取ると、その位置がキョンシーにバレます！
2. **キョンシーの手番**: 磁力で引き寄せられるように移動します。ハンターの位置を推理して追い詰めます。
3. **捕獲**: 同じマスに入ると、「カチッ」と磁石がくっつきます。これが捕まった合図！

## 勝利条件
- **ハンター**: 全てのお宝を集める。
- **キョンシー**: ハンターを全滅させる（規定回数捕まえる）。

## ポイント
- 「カチッ」という音が鳴った瞬間の悲鳴と歓声が最高に盛り上がります。
""",
        "min_players": 2,
        "max_players": 5,
        "play_time": 20,
        "min_age": 10,
        "published_year": 2022,
        "official_url": "https://magellan.official.ec/items/68310931",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Hidden Movement", "One vs Many"]
        }
    },
    {
        "title": "コードネーム",
        "title_ja": "コードネーム",
        "title_en": "Codenames",
        "summary": "「単語1つ」で複数の正解を導く、連想ゲームの傑作",
        "description": "2チームに分かれ、リーダー（スパイマスター）のヒントを元に、場に並んだ25枚の単語カードから味方のスパイを探し出します。ヒントは「単語1つ」と「枚数」だけ。敵や暗殺者（即死）を避けながら、味方全員を見つけ出せ！",
        "rules_content": """
# コードネームの遊び方

## ゲームの概要
語彙力とひらめきが試されるチーム戦ゲームです。
「海、3枚！」のようなヒントで、味方に「水」「魚」「青」などを当ててもらいます。

## ゲームの流れ
1. **準備**: 25枚の単語カードを並べます。リーダーだけが正解の場所を知っています。
2. **ヒント**: リーダーは「ヒントの単語1つ」と「枚数」を言います。
   - 例：「空、2枚」（正解は「雲」と「鳥」を想定）
3. **回答**: チームメンバーは相談して、カードを指さします。
   - **正解**: 続けて回答できます。
   - **失敗（一般人/敵）**: ターン終了。
   - **暗殺者**: 選んだらその瞬間に**即負け**です！

## 勝利条件
-先に全ての味方カードを当てたチームの勝ち。

## 初心者へのアドバイス
- 欲張って「4枚！」とか言うと、大体暗殺者を踏んで負けます。堅実に2枚ずつ当てるのがコツです。
""",
        "min_players": 2,
        "max_players": 8,
        "play_time": 15,
        "min_age": 14,
        "published_year": 2015,
        "official_url": "https://hobbyjapan.games/codenames/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Word Game", "Team-Based Game"]
        }
    },
    {
        "title": "海底探険",
        "title_ja": "海底探険",
        "title_en": "Deep Sea Adventure",
        "summary": "酸素はみんなで共有！欲張ると死ぬ、チキンレースゲーム",
        "description": "潜水艦の乗組員となり、海底の財宝を持ち帰ります。深く潜れば高得点ですが、酸素ボンベは全員で1つ！誰かが財宝を持つと酸素が激減します。「まだ行ける」「あいつが戻る前に」という欲が全滅を招く、名作ダイスゲームです。",
        "rules_content": """
# 海底探険の遊び方

## ゲームの概要
みんなで酸素を共有しながら、海底の財宝を集めるすごろく系ゲームです。
欲張りすぎると酸素が尽きて、全員溺れます（ゲームオーバー）。

## ゲームの流れ
1. **移動**: ダイスを振って進みます。
   - **重要**: 財宝を持っていると、その数だけ進める数が減ります！
2. **探索**: 止まったマスの財宝を拾うか、拾わないか選べます。
   - 拾うと、そのマスの財宝を自分の手元に置き、空いたマスは飛び越えられるようになります。
   - 逆に、手元の財宝を置いて身軽になることもできます。
3. **引き返す**: 手番中、一度だけ「引き返す」宣言ができます。一度宣言したら潜水艦に向かってしか進めません。
4. **酸素消費**: **財宝を持っている人の手番終了時、持っている数だけ酸素が減ります。**

## 勝利条件
- 3ラウンド行い、持ち帰った財宝の得点が一番高い人の勝ち。
- 酸素が尽きて潜水艦に戻れなかった場合、そのラウンドで拾った財宝は全て失います（海の藻屑）。

## ポイント
- 「行ける」と思っても、他の人が財宝を拾うと酸素が一気に減ります。早めの帰還が生存の鍵です。
""",
        "min_players": 2,
        "max_players": 6,
        "play_time": 30,
        "min_age": 8,
        "published_year": 2014,
        "official_url": "https://oinkgames.com/ja/games/analog/deep-sea-adventure/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Push Your Luck", "Roll and Move"]
        }
    },
    {
        "title": "私の世界の見方",
        "title_ja": "私の世界の見方",
        "title_en": "Wie ich die Welt sehe...",
        "summary": "お題の空欄を埋める、大喜利パーティーゲームの定番",
        "description": "親が出したお題「〇〇は世界を滅ぼす」の空欄に、手札から一番面白いと思う単語カードを出します。親の感性にハマれば得点ゲット！「もっと」版と混ぜて遊ぶこともできます。",
        "rules_content": """
# 私の世界の見方の遊び方

## ゲームの概要
親のセンスに合わせて、一番面白い回答を選ぶ大喜利ゲームです。
回答は手札から選ぶだけなので、大喜利が苦手な人でも楽しめます。

## ゲームの流れ
1. **お題**: 親がお題カードを読みます。「例：今の日本に足りないのは（　　）だ。」
2. **回答**: 子は手札から、空欄に合うと思う単語カードを裏向きで出します。
3. **選考**: 親は出されたカードをシャッフルして読み上げ、一番気に入ったものを選びます。
4. **得点**: 選ばれたカードを出した人が得点を獲得し、次の親になります。

## ポイント
- 親の性格を読むのが大事。「真面目な答え」が受けるか、「下ネタ」が受けるか？
""",
        "min_players": 2,
        "max_players": 9,
        "play_time": 30,
        "min_age": 10,
        "published_year": 2004,
        "official_url": "https://www.tg-games.info/wieich",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Voting", "Hand Management"]
        }
    },
    {
        "title": "ウボンゴ",
        "title_ja": "ウボンゴ",
        "title_en": "Ubongo",
        "summary": "パズル×スピード！脳みそが沸騰するアクションパズル",
        "description": "指定された枠に、テトリスのような形のピースを隙間なく埋めるパズルゲーム。砂時計が落ちる前に完成させ「ウボンゴ！」と叫びましょう。簡単なルールで、子供から大人まで白熱します。",
        "rules_content": """
# ウボンゴの遊び方

## ゲームの概要
制限時間内にパズルを完成させる、スピード勝負のパズルゲームです。
スワヒリ語で「脳」という意味です。

## ゲームの流れ
1. **ダイス**: ダイスを振り、今回使うピースとお題（枠の形）を決めます。
2. **パズル**: 全員一斉にパズル開始！指定されたピースを、枠にピッタリはめます。
3. **宣言**: 完成したら「ウボンゴ！」と叫びます。
4. **報酬**: 砂時計が落ちる前に完成できた人は、宝石（得点）をもらえます。早かった人はボーナスも！

## 勝利条件
- 9ラウンド行い、宝石の合計得点が高い人の勝ち。

## ポイント
- 焦ると全然ハマりません。落ち着いて！
- パズルが苦手な人用には、少し簡単な面も用意されています。
""",
        "min_players": 1,
        "max_players": 4,
        "play_time": 25,
        "min_age": 8,
        "published_year": 2003,
        "official_url": "http://www.gp-inc.jp/boardgame_ubongo.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Pattern Building", "Real-time"]
        }
    },
    {
        "title": "ブロックス",
        "title_ja": "ブロックス",
        "title_en": "Blokus",
        "summary": "角と角を繋げるだけ！世界的ベストセラーの陣取りゲーム",
        "description": "自分の色のピースを、角が接するように置いて陣地を広げていきます。ルールは「角で繋げる」「辺は接してはいけない」の2つだけ。相手の邪魔をしながら、いかに自分のピースを沢山置けるかを目指します。",
        "rules_content": """
# ブロックスの遊び方

## ゲームの概要
4色のピースを盤面に置いていく陣取りゲームです。
シンプルですが、相手の道を塞ぐなどの戦略性が高いです。

## ゲームの流れ
1. **配置**: 順番に自分のピースを1つ盤面に置きます。
2. **ルール**: 
   - 自分のピースの**「角（かど）」と「角」**がくっつくように置きます。
   - 自分のピースの**「辺（へん）」と「辺」**がくっついてはいけません。
   - 他人のピースとは、辺で接してもOKです。
3. **終了**: 全員が置けなくなったら終了です。

## 勝利条件
- 手元に残ったピースのマス目が少ない（＝沢山置けた）人の勝ち。
- 全部のピースを置けたらボーナス点！

## ポイント
- 最初は中央を目指して広げ、後半は隙間にねじ込むのがコツです。
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 20,
        "min_age": 7,
        "published_year": 2000,
        "official_url": "https://mattel.co.jp/toys/mattel_games/blokus.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Tile Placement", "Abstract Strategy"]
        }
    },
    {
        "title": "ガイスター",
        "title_ja": "ガイスター",
        "title_en": "Geister",
        "summary": "良いオバケ？悪いオバケ？シンプルな心理戦チェス",
        "description": "互いに正体のわからない8体のオバケ駒を動かし合います。青いオバケは取ってほしいけど、赤いオバケを取るとアウト！相手の心理を読み、相手の裏をかく、2人専用の心理戦ゲームです。",
        "rules_content": """
# ガイスターの遊び方

## ゲームの概要
「良いオバケ（青）」と「悪いオバケ（赤）」を使った心理戦・将棋です。
相手からは、オバケの色（正体）は見えません。

## ゲームの流れ
1. **準備**: 青4体、赤4体を自分のエリアに自由に配置します。
2. **移動**: 交互にオバケを前後左右に1マス動かします。
3. **捕獲**: 相手のオバケがいるマスに行くと、そのオバケを取ることができます。

## 勝利条件（以下のどれか1つ）
1. **脱出**: 自分の「青」オバケを、相手側の脱出マスから外に出す。
2. **全滅**: 相手の「青」オバケを4体全部取る。
3. **自爆**: 相手に自分の「赤」オバケを4体全部取らせる（相手の負け）。

## ポイント
- わざと赤オバケを強気に進めて「青かな？」と思わせたり、ブラフが重要です。
""",
        "min_players": 2,
        "max_players": 2,
        "play_time": 20,
        "min_age": 8,
        "published_year": 1982,
        "official_url": "https://mobius-games.co.jp/DreiMagier/Geister.html",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Bluffing", "Deduction"]
        }
    },
    {
        "title": "ラミィキューブ",
        "title_ja": "ラミィキューブ",
        "title_en": "Rummikub",
        "summary": "数字を並べ替える中毒性！世界中で愛される頭脳パズル",
        "description": "手持ちの数字タイルを、ルールに従って場に出していきます。場のタイルを自由に組み替えて（アレンジして）もOK！頭をフル回転させて、手持ちのタイルを全て無くした人が勝ちです。",
        "rules_content": """
# ラミィキューブの遊び方

## ゲームの概要
数字のタイルを組み合わせて場に出し、早く手札をなくすゲームです。
トランプの「セブンブリッジ」や「麻雀」に近いです。

## ゲームの流れ
1. **ドロー**: 山からタイルを引くか、
2. **プレイ**: 手札からタイルを出します（役ができている場合）。
   - **ラン**: 同じ色で連番（例：赤の3,4,5）
   - **グループ**: 違う色で同じ数字（例：赤7,青7,黄7）
3. **アレンジ**: 場に出ているタイルを自由に組み替えて、自分のタイルをくっつけることができます！これがこのゲームの醍醐味です。

## 勝利条件
- 手持ちのタイルを全て出し切った人の勝ち。

## 初心者へのアドバイス
- 最初の1回だけは「数字の合計が30以上」の役を出さないといけません（初期条件）。
- アレンジはパズルのようで最初は難しいですが、慣れると爽快です！
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 60,
        "min_age": 8,
        "published_year": 1977,
        "official_url": "https://rummikub-japan.com/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Set Collection", "Tile Placement"]
        }
    },
    {
        "title": "アトムモンスターズ",
        "title_ja": "アトムモンスターズ",
        "title_en": "Atomon",
        "summary": "化学を遊びながら学ぶ！原子結合カードバトル",
        "description": "「水素」や「炭素」などの原子カードを結合させて、水（H2O）や二酸化炭素（CO2）などの「モンスター」を召喚！化学式がそのまま必殺技になる、学習と遊びが融合したカードゲームです。",
        "rules_content": """
# アトモン（アトムモンスターズ）の遊び方

## ゲームの概要
原子（アトム）を集めて、分子（モンスター）を作る化学バトルゲームです。
遊びながら元素記号や化学式が覚えられます。

## ゲームの流れ（基本バトル）
1. **原子集め**: 手札や場から原子カード（H, O, Cなど）を集めます。
2. **合成**: 手持ちの原子で化学式を作ると、モンスターを召喚できます！
   - 例：H（水素）2つ ＋ O（酸素）1つ ＝ 水（H2O）モンスター召喚！
3. **バトル**: 召喚したモンスターの原子番号の合計などが攻撃力になります。相手と数値を比べて勝負！

## 勝利条件
- 相手より先に規定数のポイント（分子）を獲得する。

## ポイント
- 神経衰弱ルールなど、簡単な遊び方から本格的なデッキ対戦まで幅広く遊べます。
- 「水兵リーベ僕の船…」を知らなくても、色と数字合わせで遊べます。
""",
        "min_players": 2,
        "max_players": 4,
        "play_time": 20,
        "min_age": 5,
        "published_year": 2018,
        "official_url": "https://tanqfamily.com/atomon/",
        "is_official": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "structured_data": {
            "mechanics": ["Set Collection", "Educational"]
        }
    }
]

async def main():
    print(f"Starting manual population of {len(GAMES_DATA)} games...")
    
    for game in GAMES_DATA:
        print(f"Processing: {game['title']}...")
        
        # Check existence
        existing = _client.table(_TABLE).select("id").eq("title", game["title"]).execute()
        if existing.data:
            print(f"  -> SKIP: Already exists (ID: {existing.data[0]['id']})")
            continue
            
        # Insert
        try:
            # Upsert using title as key essentially, but we use title matching above.
            # We are inserting new records.
            res = _client.table(_TABLE).insert(game).execute()
            if res.data:
                print(f"  -> SUCCESS: Added (ID: {res.data[0]['id']})")
            else:
                print("  -> FAILED: No data returned from insert.")
        except Exception as e:
            print(f"  -> ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())

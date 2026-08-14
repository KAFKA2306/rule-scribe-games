export const GENERATED_CURATED_RULE_GUIDES = {
  "skull-king": {
    "reviewed": true,
    "ruleVersion": "grandpa-becks-current-2026-08-14",
    "source": {
      "label": "Grandpa Beck's Games 公式ルール",
      "url": "https://www.grandpabecksgames.com/pages/skull-king",
      "ruleVersion": "grandpa-becks-current-2026-08-14"
    },
    "facts": {
      "rounds": 10,
      "actionCount": 3,
      "suits": 4,
      "trumpSuit": "black"
    },
    "quick": {
      "win": "各ラウンドで取るトリック数をビッドし、予想どおりに取って得点する。10ラウンド終了時の合計得点を最も高くする。",
      "actions": [
        "数字カードがリードされたら、数字カードを出す場合は同じスートを持っていればそのスートを出す。特殊カードはいつでも出せる。",
        "黒は切り札。Pirateは数字カードより強く、Skull KingはPirateより強い。MermaidはSkull Kingに勝つ。",
        "Pirate・Skull King・Mermaidが同じトリックに出た場合は、順番に関係なくMermaidが勝つ。"
      ],
      "turnSteps": [
        "リード役が手札から1枚出す。",
        "時計回りに各プレイヤーが1枚ずつ出す。数字カードをフォローする場合はリードされたスートに従い、特殊カードはいつでも出せる。",
        "全員が1枚出したら最も強いカードがトリックを取り、その勝者が次のトリックをリードする。"
      ],
      "turnEndChecks": [
        "自分が取ったトリック数と、ラウンド開始時のビッドを確認する。",
        "配られたカードをすべて使ったらラウンド終了。ビッドと獲得トリック数から得点し、ビッド成功時だけボーナスを加える。"
      ],
      "end": "10ラウンド終了時に合計得点が最も高いプレイヤーが勝つ。同点なら決着するまで追加ラウンドを行う。"
    },
    "scoring": {
      "summary": "1以上のビッドは的中で1トリック20点、外すと差1トリックごとに-10点。0ビッドは成功で配札枚数×10点、失敗で配札枚数×-10点。ボーナスはビッド成功時だけ加算する。",
      "rules": [
        {
          "label": "1以上をビッド",
          "detail": "ビッドどおりなら取ったトリック1つにつき+20点。多すぎても少なすぎても、差1トリックにつき-10点。外した場合は取ったトリック自体の得点はない。"
        },
        {
          "label": "0をビッド",
          "detail": "0トリックなら、そのラウンドの配札枚数×10点。1トリック以上取ると、その配札枚数×-10点。"
        },
        {
          "label": "14のボーナス",
          "detail": "ビッド成功時、緑・黄・紫の14は各+10点、黒の14は+20点。"
        },
        {
          "label": "キャラクターボーナス",
          "detail": "ビッド成功時、PirateでMermaidを取ると各+20点、Skull KingでPirateを取ると各+30点、MermaidでSkull Kingを取ると+40点。"
        }
      ],
      "example": {
        "label": "公式ルールの0ビッド例",
        "total": 70,
        "items": [
          "第7ラウンド",
          "0をビッド",
          "0トリック成功",
          "10点 × 配札7枚 = 70点"
        ]
      }
    },
    "flow": [
      {
        "id": "deal",
        "kind": "step",
        "label": "ラウンドに応じた枚数を配る",
        "note": "通常は1枚から10枚。8人戦の第9・第10ラウンドは8枚ずつ"
      },
      {
        "id": "bid",
        "kind": "step",
        "label": "取ると思うトリック数をビッドする"
      },
      {
        "id": "lead",
        "kind": "step",
        "label": "リード役がカードを1枚出す"
      },
      {
        "id": "follow",
        "kind": "condition",
        "label": "数字カードがリードされた？",
        "branches": [
          {
            "label": "はい",
            "detail": "数字カードを出すなら、持っている限り同じスートを出す。特殊カードは出せる"
          },
          {
            "label": "いいえ",
            "detail": "特殊カードのリード規則に従う"
          }
        ]
      },
      {
        "id": "winner",
        "kind": "step",
        "label": "最も強いカードがトリックを取る"
      },
      {
        "id": "cards-left",
        "kind": "condition",
        "label": "手札が残っている？",
        "branches": [
          {
            "label": "はい",
            "detail": "トリックの勝者が次をリード"
          },
          {
            "label": "いいえ",
            "detail": "得点計算へ"
          }
        ]
      },
      {
        "id": "score-round",
        "kind": "step",
        "label": "ビッドと獲得トリック数から得点する"
      },
      {
        "id": "round-ten",
        "kind": "condition",
        "label": "10ラウンド終わった？",
        "branches": [
          {
            "label": "いいえ",
            "detail": "全カードを混ぜて次のラウンドへ"
          },
          {
            "label": "はい",
            "detail": "合計得点で勝者を決定"
          }
        ]
      },
      {
        "id": "score",
        "kind": "end",
        "label": "最高得点者が勝利。同点なら追加ラウンド"
      }
    ]
  }
}

const GUIDES = {
  ipso: {
    reviewed: true,
    ruleVersion: 'gigamic-2025-10',
    source: {
      label: 'Gigamic 公式ルール',
      url: 'https://en.gigamic.com/index.php?controller=attachment&id_attachment=668',
      ruleVersion: 'gigamic-2025-10',
    },
    facts: {
      pyramidCards: 14,
      centerChoices: 2,
      starCardBonus: 3,
    },
    quick: {
      win: '各段を左から右への昇順に整えて得点し、合計点を最も高くする。',
      turnSteps: [
        '中央の表向き2枚から1枚を選ぶ。',
        '自分のピラミッドにある裏向きカード1枚と交換する。',
        '交換で取り出したカードを表向きにして中央へ置く。',
      ],
      turnEndChecks: [
        '通常手番で交換できるのは裏向きカードだけ。いったん表向きになったカードは通常手番では交換できない。',
        '中央の2枚が好みでなくても、通常手番ではどちらか1枚を選ぶ。',
      ],
      end: '全員の14枚が表向きになったら最終処理へ進む。各自は星カードを残して+3点にするか、星カードを捨てて山札から1枚引き、表向きカード1枚と交換する機会を得る。全員がこの最終処理を終えるとゲーム終了。',
    },
    scoring: {
      summary: '各段を個別に判定する。昇順でない段は0点。昇順の混色段は1点/枚、単色段は2点/枚。得点対象の数字カード上の星は1個につき+1点。頂点の星カードを残していればさらに+3点。',
      rules: [
        { label: '1. 昇順か確認', detail: '左から右へ数字が昇順でなければ、その段は丸ごと0点。' },
        { label: '2. 色で基本点を決める', detail: '昇順の段が複数色なら1点/枚、すべて同色なら2点/枚。' },
        { label: '3. 星を加える', detail: '得点対象の段にある数字カード上の星は1個につき+1点。頂点の星カードを残していれば最後に+3点。' },
        { label: '同点処理', detail: '同点なら数字カード上の星が多いプレイヤーが勝利。それでも同点なら再戦。' },
      ],
      example: {
        label: '公式ルールブックの得点例',
        total: 26,
        items: ['星カード 3点', '2枚段 4点', '3枚段 9点', '5枚段 10点'],
      },
    },
    flow: [
      { id: 'center', kind: 'step', label: '中央の表向き2枚を見る' },
      { id: 'choose', kind: 'step', label: 'そのうち1枚を選ぶ' },
      { id: 'swap', kind: 'step', label: '自分の裏向きカード1枚と交換する', note: '表向きカードは通常手番では交換不可' },
      { id: 'return', kind: 'step', label: '取り出したカードを表向きにして中央へ置く' },
      {
        id: 'all-revealed',
        kind: 'condition',
        label: '全員の14枚がすべて表向き？',
        branches: [
          { label: 'いいえ', detail: '次のプレイヤーへ' },
          { label: 'はい', detail: '最終処理へ' },
        ],
      },
      {
        id: 'star',
        kind: 'choice',
        label: '星カードをどうする？',
        branches: [
          { label: '残す', detail: 'ゲーム終了時 +3点' },
          { label: '捨てる', detail: '山札から1枚引き、表向きカード1枚を交換できる' },
        ],
      },
      { id: 'score', kind: 'end', label: '全員の最終処理後、得点計算して終了' },
    ],
  },
  splendor: {
    reviewed: true,
    ruleVersion: 'space-cowboys-2024',
    source: {
      label: 'SPACE Cowboys / Asmodee 公式ルール',
      url: 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/12/FR_SPLENDOR_Rules.pdf',
      ruleVersion: 'space-cowboys-2024',
    },
    facts: {
      actionCount: 4,
      endThreshold: 15,
      tokenLimit: 10,
    },
    quick: {
      win: '威信ポイントを集め、終了ラウンド後に最も高い得点を持つ。',
      actions: [
        '異なる色の宝石トークンを3個取る。供給に異なる3色を取れるだけ残っていない場合は、異なる2色または1色だけ取ってよい。',
        '同じ色の宝石トークンを2個取る（その色が4個以上残っている場合）。',
        '発展カード1枚を予約し、可能なら黄金トークン1個を取る。',
        '発展カード1枚を購入する。',
      ],
      turnSteps: ['4つのアクションから1つだけ選んで実行する。'],
      turnEndChecks: [
        '手番終了時にトークンが10個を超えていれば、10個になるまで返す。',
        '貴族の条件を満たしているか確認する。貴族獲得はアクションではなく、1手番につき最大1枚。',
      ],
      end: '手番終了時に誰かが15点以上なら終了がトリガーされる。全員の手番回数が同じになるまで続け、その後に最高得点者を決める。',
    },
    scoring: {
      summary: '購入した発展カードと獲得した貴族の威信ポイントを合計する。最高得点が勝利。同点なら購入した発展カード枚数が少ない方が勝利し、それでも同点なら勝利を分かち合う。',
      rules: [
        { label: '威信ポイント', detail: '購入した発展カードと獲得した貴族の威信ポイントを合計する。' },
        { label: '終了トリガー', detail: '手番終了時に15点以上へ到達するとゲーム終了がトリガーされる。' },
        { label: '同点処理', detail: '同点者のうち購入した発展カード枚数が少ない方が勝利。それでも同点なら勝利を分かち合う。' },
      ],
    },
    flow: [
      {
        id: 'action',
        kind: 'choice',
        label: '4つのアクションから1つ選ぶ',
        branches: [
          { label: 'A', detail: '異なる3色を取る' },
          { label: 'B', detail: '同色2個を取る（残り4個以上）' },
          { label: 'C', detail: 'カードを予約 + 黄金1個（あれば）' },
          { label: 'D', detail: 'カードを1枚購入' },
        ],
      },
      { id: 'token-limit', kind: 'condition', label: '手番終了時、トークンは10個以下？', branches: [{ label: 'いいえ', detail: '10個になるまで返す' }, { label: 'はい', detail: '次へ' }] },
      { id: 'noble', kind: 'condition', label: '貴族の条件を満たした？', branches: [{ label: 'はい', detail: '貴族を1枚獲得' }, { label: 'いいえ', detail: '次へ' }] },
      { id: 'end', kind: 'condition', label: '手番終了時に15点以上？', branches: [{ label: 'はい', detail: '全員の手番回数を揃えて終了' }, { label: 'いいえ', detail: '次のプレイヤーへ' }] },
    ],
  },
}

export function validateRuleGuide(guide) {
  const errors = []

  if (!guide || guide.reviewed !== true) errors.push('guide is not reviewed')
  if (!guide?.ruleVersion) errors.push('ruleVersion is required')
  if (!guide?.source?.url?.startsWith('https://')) errors.push('https source URL is required')
  if (!guide?.source?.ruleVersion) errors.push('source ruleVersion is required')
  if (guide?.ruleVersion && guide?.source?.ruleVersion && guide.ruleVersion !== guide.source.ruleVersion) {
    errors.push('guide/source ruleVersion mismatch')
  }
  if (!Array.isArray(guide?.quick?.turnSteps) || guide.quick.turnSteps.length === 0) {
    errors.push('turnSteps are required')
  }
  if (!guide?.quick?.end) errors.push('end summary is required')
  if (!Array.isArray(guide?.flow) || guide.flow.length < 2) errors.push('flow requires at least two nodes')

  const actionCount = guide?.facts?.actionCount
  if (Number.isInteger(actionCount)) {
    if (!Array.isArray(guide?.quick?.actions) || guide.quick.actions.length !== actionCount) {
      errors.push(`action count mismatch: expected ${actionCount}`)
    }
  }

  const endThreshold = guide?.facts?.endThreshold
  if (Number.isInteger(endThreshold) && !String(guide?.quick?.end || '').includes(String(endThreshold))) {
    errors.push(`end threshold ${endThreshold} missing from summary`)
  }

  return { valid: errors.length === 0, errors }
}

export function getCuratedRuleGuide(slug) {
  const guide = GUIDES[slug]
  if (!guide) return null
  return validateRuleGuide(guide).valid ? guide : null
}

export function listCuratedRuleGuides() {
  return Object.entries(GUIDES).map(([slug, guide]) => ({ slug, guide }))
}

const GUIDES = {
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

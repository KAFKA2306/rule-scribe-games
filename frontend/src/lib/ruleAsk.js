import { getCuratedRuleGuide } from './curatedRuleGuides.js'

const INTENTS = [
  { id: 'setup', terms: ['準備', 'セットアップ', '配る', '最初に'] },
  { id: 'tie', terms: ['同点', '引き分け', 'タイブレーク'] },
  { id: 'end', terms: ['終了', '終わる', '終わり', 'ゲームエンド', '勝利条件'] },
  { id: 'score', terms: ['得点', '点数', 'スコア', '何点'] },
  { id: 'limit', terms: ['上限', '最大', '何個まで', '制限'] },
  { id: 'action', terms: ['手番', 'ターン', '何ができ', 'アクション', '行動'] },
]

function normalize(text) {
  return String(text || '').normalize('NFKC').toLowerCase().replace(/\s+/g, '')
}

function detectIntent(question) {
  const normalized = normalize(question)
  return INTENTS.find((intent) => intent.terms.some((term) => normalized.includes(normalize(term))))?.id || null
}

function evidence(source, locator, text) {
  return {
    source_url: source.url,
    source_type: 'official_rulebook',
    rule_version: source.ruleVersion,
    locator,
    text,
  }
}

function answered(slug, question, guide, locator, answer) {
  return {
    game_slug: slug,
    question,
    status: 'answered',
    answer,
    evidence: [evidence(guide.source, locator, answer)],
  }
}

export function askRule(slug, question) {
  const guide = getCuratedRuleGuide(slug)
  const trimmedQuestion = String(question || '').trim()

  if (!guide || !trimmedQuestion) {
    return { game_slug: slug, question: trimmedQuestion, status: 'unresolved', answer: null, evidence: [] }
  }

  const intent = detectIntent(trimmedQuestion)

  if (intent === 'tie') {
    const tieRule = guide.scoring?.rules?.find((rule) => normalize(rule.label).includes('同点'))
    if (tieRule?.detail) return answered(slug, trimmedQuestion, guide, `scoring:${tieRule.label}`, tieRule.detail)
  }

  if (intent === 'score' && guide.scoring?.summary) {
    return answered(slug, trimmedQuestion, guide, 'scoring:summary', guide.scoring.summary)
  }

  if (intent === 'end' && guide.quick?.end) {
    return answered(slug, trimmedQuestion, guide, 'quick:end', guide.quick.end)
  }

  if (intent === 'action') {
    const actions = guide.quick?.actions?.length ? guide.quick.actions : guide.quick?.turnSteps
    if (actions?.length) return answered(slug, trimmedQuestion, guide, 'quick:actions', actions.join(' '))
  }

  if (intent === 'limit') {
    const limitCheck = guide.quick?.turnEndChecks?.find((item) => /上限|超え|以下|まで/.test(item))
    if (limitCheck) return answered(slug, trimmedQuestion, guide, 'quick:turnEndChecks', limitCheck)

    const limitNode = guide.flow?.find((node) => /上限|超え|以下|まで/.test(`${node.label || ''} ${node.note || ''}`))
    if (limitNode?.label) return answered(slug, trimmedQuestion, guide, `flow:${limitNode.id}`, limitNode.label)
  }

  // Setup is intentionally fail-closed until the curated guide has reviewed setup evidence.
  return { game_slug: slug, question: trimmedQuestion, status: 'unresolved', answer: null, evidence: [] }
}

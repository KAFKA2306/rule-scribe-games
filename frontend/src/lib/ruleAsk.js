const INTENTS = [
  { id: 'setup', terms: ['準備', 'セットアップ', '配る', '最初に'] },
  { id: 'tie', terms: ['同点', '引き分け', 'タイブレーク'] },
  { id: 'end', terms: ['終了', '終わる', '終わり', 'ゲームエンド', '勝利条件'] },
  { id: 'score', terms: ['得点', '点数', 'スコア', '何点'] },
  { id: 'limit', terms: ['上限', '最大', '何個まで', '制限'] },
  { id: 'action', terms: ['手番', 'ターン', '何ができ', 'アクション', '行動'] },
]

const INTENT_NODE_TYPES = {
  setup: ['setup'],
  tie: ['conflict_resolution', 'exception'],
  end: ['game_end', 'victory', 'round_end'],
  score: ['scoring', 'victory'],
  limit: ['condition', 'exception', 'action'],
  action: ['action', 'turn'],
}

const TRUSTED_STATUSES = new Set(['source_bound', 'verified'])

function normalize(text) {
  return String(text || '').normalize('NFKC').toLowerCase().replace(/\s+/g, '')
}

function detectIntent(question) {
  const normalized = normalize(question)
  return INTENTS.find((intent) => intent.terms.some((term) => normalized.includes(normalize(term))))?.id || null
}

function trustedNodes(graph) {
  if (graph?.status !== 'available' || !Array.isArray(graph.nodes)) return []
  return graph.nodes.filter((node) => (
    TRUSTED_STATUSES.has(node.verification_status)
    && node.normalized_statement
    && node.source_url
  ))
}

function nodeMatchesIntent(node, intent) {
  if (!INTENT_NODE_TYPES[intent]?.includes(node.node_type)) return false
  if (intent !== 'limit') return true
  return /上限|最大|まで|以下|超え|個|枚|token|card/i.test(node.normalized_statement)
}

function evidenceFromNode(graph, node) {
  return {
    source_url: node.source_url,
    source_type: 'official_rulebook',
    rule_version: graph.source_revision || graph.rule_set_id,
    locator: node.source_locator || node.rule_id,
    text: node.normalized_statement,
  }
}

export function askRule(graph, question) {
  const trimmedQuestion = String(question || '').trim()
  const slug = graph?.slug || null
  if (!trimmedQuestion) {
    return { game_slug: slug, question: trimmedQuestion, status: 'unresolved', answer: null, evidence: [] }
  }

  const intent = detectIntent(trimmedQuestion)
  if (!intent) {
    return { game_slug: slug, question: trimmedQuestion, status: 'unresolved', answer: null, evidence: [] }
  }

  const matches = trustedNodes(graph)
    .filter((node) => nodeMatchesIntent(node, intent))
    .sort((left, right) => (left.sequence ?? Number.MAX_SAFE_INTEGER) - (right.sequence ?? Number.MAX_SAFE_INTEGER))
    .slice(0, intent === 'action' ? 4 : 2)

  if (!matches.length) {
    return { game_slug: slug, question: trimmedQuestion, status: 'unresolved', answer: null, evidence: [] }
  }

  return {
    game_slug: slug,
    question: trimmedQuestion,
    status: 'answered',
    answer: matches.map((node) => node.normalized_statement).join(' '),
    evidence: matches.map((node) => evidenceFromNode(graph, node)),
  }
}

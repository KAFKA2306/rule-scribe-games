import { test, expect } from '@playwright/test'

const piliPili = {
  id: 'game-pili-pili',
  slug: 'pili-pili',
  title: 'Pili Pili',
  title_ja: 'ピリピリ',
  summary: '予想型トリックテイキング。',
  description: 'Pili Pili',
  rules_content: 'このページは Board Game Arena（BGA）実装 を基準にしています。',
  setup_summary: 'BGA版の準備',
  gameplay_summary: 'BGA版の流れ',
  end_game_summary: 'BGA版では誰かが6ピリで終了',
  structured_data: {},
  source_url: 'https://ja.boardgamearena.com/gamepanel?game=pilipili',
  source_trust: 'authorized_partner',
  content_review_status: 'review_required',
  identity_status: 'verified',
}

const ruleSets = {
  schema_version: '1.0',
  status: 'available',
  game_id: piliPili.id,
  slug: piliPili.slug,
  rulesets: [
    {
      ruleset_id: 'bga-ruleset',
      game_id: piliPili.id,
      version: 1,
      schema_version: '1.0',
      language_code: 'ja',
      edition_label: 'BGA implementation',
      revision_label: '260623-1715',
      source_revision: 'Board Game Arena Release 260623-1715',
      platform: 'Board Game Arena',
      publisher_name: 'ATM Gaming',
      status: 'active',
      verification_status: 'source_bound',
      is_active: true,
      source_ids: ['bga:pili-pili:260623-1715'],
    },
    {
      ruleset_id: 'physical-ruleset',
      game_id: piliPili.id,
      version: 1,
      schema_version: '1.0',
      language_code: 'fr',
      edition_label: 'ATM Gaming physical product',
      platform: 'physical',
      publisher_name: 'ATM Gaming',
      status: 'active',
      verification_status: 'source_bound',
      is_active: true,
      source_ids: ['publisher:atm:pili-pili:current'],
    },
  ],
}

const bgaRuleGraph = {
  schema_version: '1.0',
  status: 'available',
  game_id: piliPili.id,
  slug: piliPili.slug,
  work_id: 'work-pili-pili',
  rule_set_id: 'bga-ruleset',
  source_revision: 'Board Game Arena Release 260623-1715',
  nodes: [{
    rule_id: 'game-end.six-pili',
    node_type: 'game_end',
    normalized_statement: 'Board Game Arena版では登録済み終了条件を使う。',
    verification_status: 'source_bound',
    source_url: 'https://ja.boardgamearena.com/gamepanel?game=pilipili',
    source_locator: 'BGA rules',
  }],
  edges: [],
}

test('Pili Pili rule questions stay inside the selected RuleSet', async ({ page }) => {
  await page.route('**/api/games/pili-pili/rule-sets', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(ruleSets),
  }))
  await page.route('**/api/games/pili-pili/rule-graph**', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(bgaRuleGraph),
  }))
  await page.route('**/api/games/pili-pili', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(piliPili),
  }))
  await page.route('**/api/games/pili-pili/glossary**', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ status: 'not_available', concepts: [] }),
  }))

  await page.goto('/games/pili-pili')

  const context = page.getByLabel('RuleSet context')
  const selector = page.getByLabel('確認するルール版:')
  const question = page.getByLabel('ルールの質問')
  const submit = page.getByRole('button', { name: '根拠付きで確認' })

  await expect(selector).toHaveValue('bga-ruleset')
  await expect(context).toContainText('表示中の本文: BGA implementation · Board Game Arena · ja · 260623-1715 · source_bound')
  await expect(question).toBeEnabled()

  await selector.selectOption('physical-ruleset')

  await expect(context).toContainText('ATM Gaming physical product · physical · fr の質問回答用projectionは未整備です')
  await expect(context).toContainText('別版の登録済み回答を流用しません')
  await expect(question).toBeDisabled()
  await expect(submit).toBeDisabled()

  await selector.selectOption('bga-ruleset')
  await expect(question).toBeEnabled()
})

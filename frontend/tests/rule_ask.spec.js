import { test, expect } from '@playwright/test'

const officialRuleUrl = 'https://publisher.example/splendor-rules.pdf'

const splendor = {
  id: 'game-splendor',
  slug: 'splendor',
  title: 'Splendor',
  title_ja: '宝石の煌き',
  min_players: 2,
  max_players: 4,
  play_time: 30,
  min_age: 10,
  published_year: 2014,
  summary: '宝石を集めて発展カードを購入し、威信ポイントを競うゲーム。',
  rules_content: '# Rules',
  identity_status: 'verified',
  source_trust: 'official_publisher',
  content_review_status: 'publisher_reviewed',
  structured_data: {},
}

const ruleGraph = {
  schema_version: '1.0',
  status: 'available',
  game_id: splendor.id,
  slug: splendor.slug,
  work_id: 'work-splendor',
  rule_set_id: 'splendor-current',
  source_revision: 'official-rules-v1',
  nodes: [
    {
      rule_id: 'action.take-three',
      node_type: 'action',
      normalized_statement: '異なる色の宝石トークンを3個取る。',
      sequence: 1,
      verification_status: 'source_bound',
      source_url: officialRuleUrl,
      source_locator: 'p.2 action',
    },
    {
      rule_id: 'game-end.15',
      node_type: 'game_end',
      normalized_statement: '15点以上のプレイヤーが出たラウンドの終了時にゲームが終わる。',
      verification_status: 'source_bound',
      source_url: officialRuleUrl,
      source_locator: 'p.3 end',
    },
    {
      rule_id: 'score.prestige',
      node_type: 'scoring',
      normalized_statement: '発展カードと貴族タイルの威信ポイントを合計する。',
      verification_status: 'verified',
      source_url: officialRuleUrl,
      source_locator: 'p.3 scoring',
    },
    {
      rule_id: 'tie.cards',
      node_type: 'conflict_resolution',
      normalized_statement: '同点なら購入した発展カード枚数が少ない方を上位とする。',
      verification_status: 'source_bound',
      source_url: officialRuleUrl,
      source_locator: 'p.3 tie',
    },
    {
      rule_id: 'limit.tokens',
      node_type: 'condition',
      normalized_statement: '手番終了時のトークン上限は10個。',
      verification_status: 'source_bound',
      source_url: officialRuleUrl,
      source_locator: 'p.2 token limit',
    },
  ],
  edges: [],
}

async function mockSplendor(page) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/splendor') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: splendor }) })
      return
    }
    if (url.pathname === '/api/games/splendor/rule-graph') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ruleGraph) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

async function ask(page, question) {
  const input = page.getByRole('searchbox', { name: 'ルールの質問' })
  await input.fill(question)
  await page.getByRole('button', { name: '根拠付きで確認' }).click()
}

test('answers turn action from the current canonical RuleGraph', async ({ page }) => {
  await mockSplendor(page)
  await page.goto('/games/splendor')
  await expect(page.getByText('ルールを質問', { exact: true })).toBeVisible()
  await ask(page, '手番では何ができる？')

  const answer = page.getByRole('status').filter({ hasText: '異なる色の宝石トークンを3個取る' })
  await expect(answer).toBeVisible()
  const evidence = page.getByRole('link', { name: '公式ルールを確認' })
  await expect(evidence).toHaveAttribute('href', officialRuleUrl)
  await expect(page.getByText(/p\.2 action/)).toBeVisible()
})

test('answers end, scoring, tie and token-limit questions from verified nodes', async ({ page }) => {
  await mockSplendor(page)
  await page.goto('/games/splendor')

  await ask(page, 'ゲームはいつ終わる？')
  await expect(page.getByRole('status').filter({ hasText: '15点以上' })).toBeVisible()

  await ask(page, '得点はどう数える？')
  await expect(page.getByRole('status').filter({ hasText: '威信ポイント' })).toBeVisible()

  await ask(page, '同点ならどうなる？')
  await expect(page.getByRole('status').filter({ hasText: '購入した発展カード枚数が少ない方' })).toBeVisible()

  await ask(page, 'トークンは何個まで？')
  await expect(page.getByRole('status').filter({ hasText: '10個' })).toBeVisible()
})

test('fails closed when verified setup evidence is unavailable', async ({ page }) => {
  await mockSplendor(page)
  await page.goto('/games/splendor')
  await ask(page, 'セットアップはどうする？')

  await expect(page.getByText('この質問に答えられる確認済みRuleGraph根拠がありません。公式ルール本文を確認してください。')).toBeVisible()
})

test('fails closed when canonical RuleGraph is unavailable', async ({ page }) => {
  const otherGame = { ...splendor, slug: 'unknown-game', title_ja: '別ゲーム' }
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/unknown-game') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: otherGame }) })
      return
    }
    if (url.pathname === '/api/games/unknown-game/rule-graph') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ schema_version: '1.0', status: 'not_available', game_id: 'other', slug: 'unknown-game', nodes: [], edges: [] }),
      })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/unknown-game')
  await expect(page.getByText('ルールを質問', { exact: true })).toBeVisible()
  await ask(page, '同点なら？')
  await expect(page.getByText('この質問に答えられる確認済みRuleGraph根拠がありません。公式ルール本文を確認してください。')).toBeVisible()
})

test('canonical RuleGraph question flow works at mobile width', async ({ page }) => {
  await mockSplendor(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/games/splendor')

  await expect(page.getByRole('heading', { name: '宝石の煌き' })).toBeVisible()
  await expect(page.getByText('ルールを質問', { exact: true })).toBeVisible()
  await ask(page, '同点なら？')
  await expect(page.getByRole('status').filter({ hasText: '購入した発展カード枚数が少ない方' })).toBeVisible()
  await expect(page.getByRole('link', { name: '公式ルールを確認' })).toBeVisible()
})

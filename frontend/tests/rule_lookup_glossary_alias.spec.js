import { test, expect } from '@playwright/test'

const game = {
  id: 902,
  slug: 'rule-lookup-alias-test',
  title: 'Rule Lookup Alias Test',
  title_ja: 'ルール検索別名テスト',
  min_players: 2,
  max_players: 8,
  play_time: 45,
  min_age: 8,
  published_year: 2026,
  summary: '正準用語集の別名から確認済みルールへ移動するテスト。',
  source_url: 'https://example.com/source',
  source_trust: 'official_publisher',
  content_review_status: 'human_reviewed',
  rules_content: '# Rules\n\n## 得点\n\n0を宣言した場合の得点を計算します。',
  structured_data: {},
}

const glossary = {
  status: 'available',
  entries: [
    {
      concept_id: 'player-action.bid',
      label: 'ビッド',
      definition: '獲得するトリック数の宣言です。',
      aliases: ['Bid'],
      rule_references: [
        {
          rule_id: 'scoring.bid-one-plus',
          rule_set_id: 'ruleset-current',
          normalized_statement: '1以上をビッドした場合の得点を計算します。',
          reference_kind: 'defines',
          verification_status: 'source_bound',
          source_url: 'https://example.com/official-rulebook',
        },
        {
          rule_id: 'scoring.bid-zero',
          rule_set_id: 'ruleset-current',
          normalized_statement: '0ビッドを宣言した場合は、0ビッド用の得点計算を行います。',
          reference_kind: 'mentions',
          verification_status: 'source_bound',
          source_url: 'https://example.com/official-rulebook',
        },
      ],
    },
  ],
}

test('ルール内検索で正準用語集の英語別名と確認済みRuleNodeから同じConceptへ到達する', async ({ page }) => {
  let glossaryRequests = 0

  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url())

    if (url.pathname === '/api/games/rule-lookup-alias-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === '/api/games/rule-lookup-alias-test/glossary') {
      glossaryRequests += 1
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(glossary) })
      return
    }
    if (url.pathname === '/api/games/rule-lookup-alias-test/presentation') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          rule_set_id: 'ruleset-current',
          setup: { status: 'not_available', items: [] },
          game_flow: { status: 'not_available', items: [] },
          end_condition: { status: 'not_available', items: [] },
          scoring: {
            status: 'available',
            items: [
              { rule_id: 'scoring.bid-one-plus', text: '1以上をビッドした場合の得点を計算します。' },
              { rule_id: 'scoring.bid-zero', text: '0ビッドを宣言した場合は、0ビッド用の得点計算を行います。' },
            ],
          },
        }),
      })
      return
    }
    if (url.pathname === '/api/concepts/player-action.bid') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ concept_id: 'player-action.bid', game_backlinks: [] }) })
      return
    }
    if (url.pathname.endsWith('/connections')) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'not_available', connections: [] }) })
      return
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/rule-lookup-alias-test#rules')

  const ruleSearch = page.getByRole('searchbox', { name: '裁定・用語を入力' })
  await ruleSearch.fill('0 bid')
  await expect(page.getByRole('link', { name: 'ビッド', exact: true })).toBeVisible()

  await ruleSearch.fill('Bid')
  await expect(page.getByRole('link', { name: 'ビッド', exact: true })).toBeVisible()
  await page.getByRole('link', { name: 'ビッド', exact: true }).click()

  const glossaryPanel = page.locator('[aria-label="用語集"]')
  await expect(glossaryPanel.getByRole('button', { name: 'ビッド', exact: true })).toHaveAttribute('aria-expanded', 'true')
  await expect(glossaryPanel.getByText('1以上をビッドした場合の得点を計算します。', { exact: true })).toBeVisible()
  await expect(glossaryPanel.getByText('0ビッドを宣言した場合は、0ビッド用の得点計算を行います。', { exact: true })).toBeVisible()
  await expect(glossaryPanel.getByRole('link', { name: '詳しいルールで確認', exact: true }).first()).toHaveAttribute('href', '#rule-node-scoring.bid-one-plus')

  await glossaryPanel.getByRole('link', { name: '詳しいルールで確認', exact: true }).first().click()
  await expect(page.locator('#rule-node-scoring\\.bid-one-plus')).toContainText('1以上をビッドした場合の得点を計算します。')
  expect(glossaryRequests).toBe(1)
})

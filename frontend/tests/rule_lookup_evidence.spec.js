import { test, expect } from '@playwright/test'

const game = {
  id: 902,
  slug: 'source-search-test',
  title: 'Source Search Test',
  title_ja: '出典検索テスト',
  min_players: 2,
  max_players: 4,
  play_time: 30,
  min_age: 10,
  published_year: 2026,
  summary: 'ルール検索の出典表示を確認するテスト用ゲーム。',
  source_url: 'https://example.com/source',
  source_trust: 'official_publisher',
  content_review_status: 'review_required',
  rules_content: '# Rules\n\n## 進行\n\n通常の進行です。',
  structured_data: {},
}

async function mockData(page) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/source-search-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === '/api/games/source-search-test/glossary') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          entries: [
            {
              concept_id: 'faq-ruling',
              label: '特殊カードの裁定',
              definition: '特殊カードが同時に出た場合の裁定です。',
              aliases: ['Mermaid'],
              rule_references: [{
                rule_id: 'resolution.mermaid-triad',
                normalized_statement: 'Mermaidがそのトリックに勝ちます。',
                verification_status: 'source_bound',
                rule_set_id: 'current-rules',
                source_url: 'https://example.com/faq',
                source_locator: 'game:faq:mermaid-triad',
              }],
            },
            {
              concept_id: 'rulebook-rule',
              label: 'ビッド',
              definition: '獲得するトリック数を宣言します。',
              aliases: ['Bid'],
              rule_references: [{
                rule_id: 'round.bid',
                normalized_statement: '全員が同時にビッドを公開します。',
                verification_status: 'source_bound',
                rule_set_id: 'current-rules',
                source_url: 'https://example.com/rulebook',
                source_locator: 'game:rulebook:bidding',
              }],
            },
            {
              concept_id: 'two-player-ruling',
              label: '2人用の裁定',
              definition: '2人のときだけ適用する裁定です。',
              aliases: [],
              rule_references: [{
                rule_id: 'two-player.rule',
                normalized_statement: 'この裁定は該当する2人戦で適用します。',
                verification_status: 'source_bound',
                rule_set_id: 'current-rules',
                player_count: 2,
                source_url: 'https://example.com/faq-two-player',
                source_locator: 'game:faq:two-player',
              }],
            },
            {
              concept_id: 'unverified-faq',
              label: '未確認裁定',
              definition: '未確認です。',
              aliases: [],
              rule_references: [{
                rule_id: 'unverified.rule',
                normalized_statement: '未確認のFAQ記述です。',
                verification_status: 'unknown',
                source_locator: 'game:faq:unverified',
              }],
            },
          ],
        }),
      })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('確認済みのFAQ・ルールブック・人数条件を同じ検索面で区別する', async ({ page }) => {
  await mockData(page)
  await page.goto('/games/source-search-test#rules')

  const search = page.getByRole('searchbox', { name: '裁定・用語を入力' })
  const results = page.getByRole('list', { name: '用語集の検索結果' })

  await search.fill('FAQ Mermaid')
  await expect(results.getByRole('link', { name: '特殊カードの裁定' })).toBeVisible()
  await expect(results.getByText('出典: FAQ', { exact: true })).toBeVisible()
  await expect(results.getByRole('link', { name: 'ビッド' })).toHaveCount(0)
  await expect(results.getByRole('link', { name: '未確認裁定' })).toHaveCount(0)

  await search.fill('ルールブック Bid')
  await expect(results.getByRole('link', { name: 'ビッド' })).toBeVisible()
  await expect(results.getByText('出典: ルールブック', { exact: true })).toBeVisible()
  await expect(results.getByRole('link', { name: '特殊カードの裁定' })).toHaveCount(0)

  await search.fill('FAQ 2人')
  await expect(results.getByRole('link', { name: '2人用の裁定' })).toBeVisible()
  await expect(results.getByText('人数条件: 2人', { exact: true })).toBeVisible()
  await expect(results.getByText('出典: FAQ', { exact: true })).toBeVisible()
})

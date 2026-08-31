import { test, expect } from '@playwright/test'

const game = {
  id: 901,
  slug: 'glossary-test',
  title: 'Glossary Test',
  title_ja: '用語集テスト',
  min_players: 2,
  max_players: 4,
  play_time: 30,
  min_age: 10,
  published_year: 2026,
  summary: '用語集表示の回帰テスト用ゲーム。',
  source_url: 'https://example.com/source',
  source_trust: 'official_publisher',
  content_review_status: 'review_required',
  rules_content: '# Rules\n\n## 得点\n\n得点を計算します。',
  structured_data: {
    keywords: [{ term: '旧データの用語', description: '正準用語集ではない旧データ' }],
  },
}

async function mockGameAndGlossary(page, glossaryResponse) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/glossary-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === '/api/games/glossary-test/glossary') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(glossaryResponse) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('正準用語集が未整備なら旧keywordsへ戻らず未整備を明示する', async ({ page }) => {
  await mockGameAndGlossary(page, { status: 'not_available', entries: [] })
  await page.goto('/games/glossary-test#rules')

  const glossary = page.getByRole('complementary', { name: '補足情報' }).getByLabel('用語集')
  await expect(glossary.getByRole('status')).toHaveText('用語集の正準データは未整備です。')
  await expect(page.getByText('旧データの用語')).toHaveCount(0)
})

test('旧keywordsがなくても正準用語集がavailableなら表示する', async ({ page }) => {
  const gameWithoutLegacyKeywords = {
    ...game,
    structured_data: { keywords: [] },
  }

  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/glossary-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: gameWithoutLegacyKeywords }) })
      return
    }
    if (url.pathname === '/api/games/glossary-test/glossary') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          entries: [{ concept_id: 'scoring', label: '得点', definition: 'ゲームの得点に関する用語です。', aliases: [] }],
        }),
      })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/glossary-test#rules')
  const glossary = page.getByRole('complementary', { name: '補足情報' }).getByLabel('用語集')
  await expect(glossary.getByRole('button', { name: '得点', exact: true })).toBeVisible()
})
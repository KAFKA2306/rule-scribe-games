import { test, expect } from '@playwright/test'

const splendor = {
  id: 1,
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

async function mockSplendor(page) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/splendor') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: splendor }) })
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

test('answers turn action from the current game official guide', async ({ page }) => {
  await mockSplendor(page)
  await page.goto('/games/splendor')
  await ask(page, '手番では何ができる？')

  const answer = page.getByRole('status').filter({ hasText: '異なる色の宝石トークンを3個取る' })
  await expect(answer).toBeVisible()
  const evidence = page.getByRole('link', { name: '公式ルールを確認' })
  await expect(evidence).toHaveAttribute('href', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/12/FR_SPLENDOR_Rules.pdf')
  await expect(page.getByText(/quick:actions/)).toBeVisible()
})

test('answers end, scoring, tie and token-limit questions with evidence', async ({ page }) => {
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

test('fails closed when reviewed setup evidence is unavailable', async ({ page }) => {
  await mockSplendor(page)
  await page.goto('/games/splendor')
  await ask(page, 'セットアップはどうする？')

  await expect(page.getByText('この質問に答えられる確認済み根拠がありません。公式ルール本文を確認してください。')).toBeVisible()
  await expect(page.getByRole('link', { name: '公式ルールを確認' })).toHaveCount(0)
})

test('does not reuse another game guide', async ({ page }) => {
  const otherGame = { ...splendor, slug: 'unknown-game', title_ja: '別ゲーム' }
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/unknown-game') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: otherGame }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/unknown-game')
  await ask(page, '同点ならどうなる？')

  await expect(page.getByText('この質問に答えられる確認済み根拠がありません。公式ルール本文を確認してください。')).toBeVisible()
  await expect(page.getByText(/購入した発展カード枚数が少ない方/)).toHaveCount(0)
})

test('critical path works at mobile width', async ({ page }) => {
  await mockSplendor(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/games/splendor')

  await expect(page.getByRole('heading', { name: '宝石の煌き' })).toBeVisible()
  await expect(page.getByText('ルールを質問', { exact: true })).toBeVisible()
  await ask(page, '同点なら？')
  await expect(page.getByRole('status').filter({ hasText: '購入した発展カード枚数が少ない方' })).toBeVisible()
  await expect(page.getByRole('link', { name: '公式ルールを確認' })).toBeVisible()
})

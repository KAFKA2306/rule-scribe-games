import { test, expect } from '@playwright/test'

const games = [
  { id: '11111111-1111-4111-8111-111111111111', slug: 'game-one', title: 'Game One', title_ja: 'ゲーム1', summary: '1番目', min_players: 2, max_players: 4, play_time: 45, published_year: 2026, structured_data: {} },
  { id: '22222222-2222-4222-8222-222222222222', slug: 'game-two', title: 'Game Two', title_ja: 'ゲーム2', summary: '2番目', min_players: 2, max_players: 4, play_time: 60, published_year: 2026, structured_data: {} },
  { id: '33333333-3333-4333-8333-333333333333', slug: 'game-three', title: 'Game Three', title_ja: 'ゲーム3', summary: '3番目', min_players: 2, max_players: 4, play_time: 75, published_year: 2026, structured_data: {} },
  { id: '44444444-4444-4444-8444-444444444444', slug: 'game-four', title: 'Game Four', title_ja: 'ゲーム4', summary: '4番目', min_players: 2, max_players: 4, play_time: 90, published_year: 2026, structured_data: {} },
]

test.beforeEach(async ({ page }) => {
  await page.route('**/api/games?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games, total: games.length }),
    })
  })
})

test('compare limit is explicit, accessible, and blocks a fourth game until one is removed', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('ゲーム1', { exact: true }).first()).toBeVisible()

  const first = page.getByRole('button', { name: 'ゲーム1を比較に追加する' })
  const second = page.getByRole('button', { name: 'ゲーム2を比較に追加する' })
  const third = page.getByRole('button', { name: 'ゲーム3を比較に追加する' })
  const fourth = page.getByRole('button', { name: 'ゲーム4を比較に追加する' })

  await expect(page.getByRole('status')).toContainText('比較 0/3')
  await expect(first).toHaveAttribute('aria-pressed', 'false')

  await first.click()
  await second.click()
  await third.click()

  await expect(page.getByRole('status')).toContainText('比較 3/3 · 上限です')
  await expect(page.getByRole('button', { name: 'ゲーム1を比較から外す' }).first()).toHaveAttribute('aria-pressed', 'true')
  await expect(fourth).toBeDisabled()
  await expect(fourth).toHaveText('LIMIT 3')
  await expect(page.locator('.compare-item')).toHaveCount(3)

  await fourth.evaluate((button) => button.click())
  await expect(page.locator('.compare-item')).toHaveCount(3)
  await expect(fourth).toHaveAttribute('aria-pressed', 'false')

  const trayRemoveFirst = page.locator('.compare-item').getByRole('button', { name: 'ゲーム1を比較から外す' })
  await expect(trayRemoveFirst).toBeVisible()
  await trayRemoveFirst.click()

  await expect(page.getByRole('status')).toContainText('比較 2/3 · 最大3件')
  await expect(fourth).toBeEnabled()
  await fourth.click()

  await expect(page.getByRole('button', { name: 'ゲーム4を比較から外す' }).first()).toHaveAttribute('aria-pressed', 'true')
  await expect(page.locator('.compare-item')).toHaveCount(3)
})

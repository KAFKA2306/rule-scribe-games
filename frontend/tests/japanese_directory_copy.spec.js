import { test, expect } from '@playwright/test'

const GAMES = [
  {
    id: '11111111-1111-4111-8111-111111111111',
    slug: 'game-one',
    title: 'Game One',
    title_ja: 'ゲーム1',
    summary: '概要1',
    min_players: 2,
    max_players: 4,
    play_time: 30,
    strategy_tier: 'A',
    structured_data: { mechanics: ['Trick-taking'] },
  },
  {
    id: '22222222-2222-4222-8222-222222222222',
    slug: 'game-two',
    title: 'Game Two',
    title_ja: 'ゲーム2',
    summary: null,
    min_players: 3,
    max_players: 5,
    play_time: 45,
    strategy_tier: 'B',
    structured_data: { mechanics: ['Drafting'] },
  },
]

async function mockDirectory(page) {
  await page.route('**/api/games?limit=20000&offset=0', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games: GAMES, total: GAMES.length }),
    })
  })
}

test('directory and comparison use Japanese action, status, and section labels', async ({ page }) => {
  await mockDirectory(page)
  await page.goto('/')

  await expect(page.locator('html')).toHaveAttribute('lang', 'ja')
  await expect(page.getByText('2件のゲーム', { exact: true })).toBeVisible()
  await expect(page.getByText('2件', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: 'ゲーム1を比較に追加' }).click()
  await page.getByRole('button', { name: 'ゲーム2を比較に追加' }).click()

  await expect(page.getByText('比較トレイ · 2/3', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '比較する' })).toBeVisible()
  await page.getByRole('button', { name: '比較する' }).click()

  await expect(page.getByRole('heading', { name: 'ゲーム比較' })).toBeVisible()
  await expect(page.getByRole('button', { name: '比較を閉じる' })).toBeVisible()
  await expect(page.getByText('概要', { exact: true })).toHaveCount(2)
  await expect(page.getByText('基本情報', { exact: true })).toHaveCount(2)
  await expect(page.getByText('メカニクス', { exact: true })).toHaveCount(2)
  await expect(page.getByText('概要はまだありません。', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: '詳しい情報を見る' })).toHaveCount(2)

  for (const legacyText of [
    'COMPARISON BATTLE',
    'CLOSE BATTLE',
    'Synopsis',
    'Specs',
    'Mechanics',
    'VIEW FULL ANALYSIS',
    'BATTLE TRAY',
    'BATTLE START',
  ]) {
    await expect(page.getByText(legacyText, { exact: true })).toHaveCount(0)
  }
})

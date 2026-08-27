import { test, expect } from '@playwright/test'

const GAMES = [
  {
    id: '11111111-1111-4111-8111-111111111111',
    slug: 'official-game',
    title: 'Official Game',
    title_ja: '公式ゲーム',
    summary: '確認済み概要',
    identity_status: 'verified',
    content_review_status: 'human_reviewed',
    source_trust: 'official_publisher',
    min_players: 2,
    max_players: 4,
    play_time: 30,
    structured_data: { mechanics: ['Set Collection'] },
  },
  {
    id: '22222222-2222-4222-8222-222222222222',
    slug: 'unknown-source-game',
    title: 'Unknown Source Game',
    title_ja: '出典未確認ゲーム',
    summary: '確認済み概要',
    identity_status: 'verified',
    content_review_status: 'human_reviewed',
    source_trust: 'unknown',
    min_players: 2,
    max_players: 4,
    play_time: 30,
  },
  {
    id: '33333333-3333-4333-8333-333333333333',
    slug: 'third-party-game',
    title: 'Third Party Game',
    title_ja: '第三者出典ゲーム',
    summary: '確認済み概要',
    identity_status: 'verified',
    content_review_status: 'publisher_reviewed',
    source_trust: 'third_party',
    min_players: 2,
    max_players: 4,
    play_time: 30,
  },
]

async function mockDirectory(page) {
  await page.route('**/api/games?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games: GAMES, total: GAMES.length }),
    })
  })
}

test('source provenance remains visible in directory and comparison', async ({ page }) => {
  await mockDirectory(page)
  await page.goto('/')

  const officialCard = page.locator('.asset-card-shell').filter({ hasText: '公式ゲーム' })
  const unknownCard = page.locator('.asset-card-shell').filter({ hasText: '出典未確認ゲーム' })
  const thirdPartyCard = page.locator('.asset-card-shell').filter({ hasText: '第三者出典ゲーム' })

  await expect(officialCard.getByText('出典未確認', { exact: true })).toHaveCount(0)
  await expect(officialCard.getByText('第三者出典', { exact: true })).toHaveCount(0)
  await expect(unknownCard.getByText('出典未確認', { exact: true })).toBeVisible()
  await expect(thirdPartyCard.getByText('第三者出典', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: '公式ゲームを比較に追加' }).click()
  await page.getByRole('button', { name: '出典未確認ゲームを比較に追加' }).click()
  await page.getByRole('button', { name: '比較する' }).click()

  await expect(page.getByText('出典未確認', { exact: true })).toBeVisible()
  await expect(page.getByLabel('人数の根拠')).toHaveCount(2)
  await expect(page.getByLabel('時間の根拠')).toHaveCount(2)
  await expect(page.getByLabel('メカニクスの根拠')).toHaveCount(1)
  await expect(page.getByText('根拠未登録', { exact: true })).toHaveCount(5)
})

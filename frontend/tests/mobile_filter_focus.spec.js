import { test, expect } from '@playwright/test'

async function mockDirectory(page) {
  await page.route('**/api/games?limit=20000&offset=0', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        games: [
          {
            id: '11111111-1111-4111-8111-111111111111',
            slug: 'game-one',
            title: 'Game One',
            title_ja: 'ゲーム1',
            summary: 'summary',
            min_players: 2,
            max_players: 4,
          },
        ],
        total: 1,
      }),
    })
  })
}

test.use({ viewport: { width: 375, height: 812 } })

test('mobile filters move, contain, and restore keyboard focus', async ({ page }) => {
  await mockDirectory(page)
  await page.goto('/')

  const toggle = page.getByRole('button', { name: 'フィルター', exact: true })
  await toggle.click()

  const dialog = page.getByRole('dialog', { name: 'ゲーム絞り込み' })
  const close = dialog.getByRole('button', { name: 'フィルターを閉じる' })
  const reset = dialog.getByRole('button', { name: 'フィルターをリセット' })

  await expect(dialog).toBeVisible()
  await expect(close).toBeFocused()

  await page.keyboard.press('Shift+Tab')
  await expect(reset).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(close).toBeFocused()

  await page.keyboard.press('Escape')
  await expect(toggle).toBeFocused()
  await expect(page.locator('#directory-filters')).not.toHaveClass(/mobile-open/)
})

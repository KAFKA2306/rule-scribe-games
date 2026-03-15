import { test, expect } from '@playwright/test'
test.describe('Background and Search Verification', () => {
  test('should display games background and correct placeholder', async ({ page }) => {
    await page.route('**/api/games*', async (route) => {
      const json = {
        games: [
          { slug: 'catan', title: 'Catan' },
          { slug: 'splendor', title: 'Splendor' },
          { slug: 'wing-span', title: 'Wing Span' },
          { slug: 'game-4', title: 'Game 4' },
          { slug: 'game-5', title: 'Game 5' },
        ],
      }
      await route.fulfill({ json })
    })
    page.on('console', (msg) => console.log(`BROWSER LOG: ${msg.text()}`))
    page.on('pageerror', (err) => console.log(`BROWSER ERROR: ${err}`))
    await page.goto('http://localhost:5173')
    const errorBanner = page.locator('.error-banner')
    if (await errorBanner.isVisible()) {
      console.log('Error Banner Text:', await errorBanner.textContent())
    }
    const container = page.locator('.game-background-container')
    await expect(container).toBeVisible()
    const grid = page.locator('.game-background-grid')
    await expect(grid).toBeVisible()
    await expect(grid).toHaveCSS('opacity', '0.5')
    const tiles = page.locator('.bg-game-tile')
    await expect(tiles.first()).toBeVisible()
    const count = await tiles.count()
    expect(count).toBeGreaterThan(10)
    const searchInput = page.locator('.search-input')
    await expect(searchInput).toBeVisible()
    const expectedPlaceholder = 'ボードゲーム名を入れてね。なければ調べるよ！'
    await expect(searchInput).toHaveAttribute('placeholder', expectedPlaceholder)
  })
})

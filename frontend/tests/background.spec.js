import { test, expect } from '@playwright/test'

test.describe('Background and Search Verification', () => {
  test('should display games background and correct placeholder', async ({ page }) => {
    // Mock the API response
    await page.route('**/api/games*', async (route) => {
      const json = {
        games: [
          { slug: 'catan', title: 'Catan' },
          { slug: 'splendor', title: 'Splendor' },
          { slug: 'wing-span', title: 'Wing Span' },
          // Add enough to trigger the loop/shuffle logic if needed,
          // but the component logic duplicates if < 50, so a few is fine.
          { slug: 'game-4', title: 'Game 4' },
          { slug: 'game-5', title: 'Game 5' },
        ],
      }
      await route.fulfill({ json })
    })

    // Debug console logs
    page.on('console', (msg) => console.log(`BROWSER LOG: ${msg.text()}`))
    page.on('pageerror', (err) => console.log(`BROWSER ERROR: ${err}`))

    // Navigate to the local dev server
    await page.goto('http://localhost:5173')

    // Check for error banner
    const errorBanner = page.locator('.error-banner')
    if (await errorBanner.isVisible()) {
      console.log('Error Banner Text:', await errorBanner.textContent())
    }

    // 1. Verify Background
    // Check if the container exists
    const container = page.locator('.game-background-container')
    await expect(container).toBeVisible()

    // Check if the grid exists
    const grid = page.locator('.game-background-grid')
    await expect(grid).toBeVisible()

    // Check visibility of tiles using CSS properties that we set (opacity/filter)
    // We expect the grid to have specific styles
    await expect(grid).toHaveCSS('opacity', '0.35')
    // Note: computed filter values can vary by browser (e.g. "grayscale(0.6) sepia(0.2)"), so we might skip exact filter assertion or make it loose.

    // Check if there are game tiles
    // We wait for at least one tile to be present
    const tiles = page.locator('.bg-game-tile')
    await expect(tiles.first()).toBeVisible()

    // Check that we have a decent number of tiles (we duplicate to 50+, so assume > 10)
    const count = await tiles.count()
    expect(count).toBeGreaterThan(10)

    // 2. Verify Search Placeholder
    const searchInput = page.locator('.search-input')
    await expect(searchInput).toBeVisible()

    const expectedPlaceholder = 'ボードゲーム名を入れてね。なければ調べるよ！'
    await expect(searchInput).toHaveAttribute('placeholder', expectedPlaceholder)
  })
})

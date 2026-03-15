import { test, expect } from '@playwright/test'
test('should allow manual editing of game details', async ({ page }) => {
  await page.goto('http://localhost:5173')
  await expect(page.locator('.loading-spinner')).not.toBeVisible()
  await page.click('button[title="編集"]')
  const uniqueTitle = `Updated Title ${Date.now()}`
  await page.fill('input[name="title"]', uniqueTitle)
  await page.fill('input[name="title_ja"]', uniqueTitle)
  await page.fill('textarea[name="summary"]', 'Updated Summary')
  await page.click('button[type="submit"]')
  await expect(page.locator('.modal-overlay')).not.toBeVisible()
  await expect(page.locator('h1.game-title')).toHaveText(uniqueTitle)
})

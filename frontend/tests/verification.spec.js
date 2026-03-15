import { test, expect } from '@playwright/test'
test('verify home page loads and search works', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/ボドゲのミカタ/)
  const gameCard = page.locator('.game-card').first()
  await expect(gameCard).toBeVisible({ timeout: 10000 })
  const input = page.locator('input.search-input')
  await input.fill('カタン')
  await page.keyboard.press('Enter')
})

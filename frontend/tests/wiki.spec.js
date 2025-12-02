import { test, expect } from '@playwright/test'

test.describe('Wiki Generation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://rule-scribe-games.vercel.app')
  })

  test.afterEach(async ({ page }, testInfo) => {
    if (testInfo.status !== 'passed') {
      const name = testInfo.title.replace(/\s+/g, '_').toLowerCase()
      await page.screenshot({ path: `test-results/${name}_failure.png` })
    }
  })

  test('verify Catan', async ({ page }) => {
    await page.getByPlaceholder('ゲームの名前を入れてね').fill('Catan')
    await page.getByRole('button', { name: 'さがす' }).click()

    const result = page.locator('.results li').filter({ hasText: 'Catan' }).first()
    await result.waitFor({ timeout: 60000 })
    await result.click()

    await expect(page.locator('.detail-head h2')).toContainText('Catan', { timeout: 10000 })
    await expect(page.getByRole('button', { name: /要約する|要約完了！/ })).toBeVisible()
  })

  test('verify Dominion', async ({ page }) => {
    await page.getByPlaceholder('ゲームの名前を入れてね').fill('Dominion')
    await page.getByRole('button', { name: 'さがす' }).click()

    const result = page.locator('.results li').filter({ hasText: 'Dominion' }).first()
    await result.waitFor({ timeout: 60000 })
    await result.click()

    await expect(page.locator('.detail-head h2')).toContainText('Dominion', { timeout: 10000 })
    await expect(page.getByRole('button', { name: /要約する|要約完了！/ })).toBeVisible()
  })

  test('verify Space Base', async ({ page }) => {
    await page.getByPlaceholder('ゲームの名前を入れてね').fill('Space Base')
    await page.getByRole('button', { name: 'さがす' }).click()

    const result = page.locator('.results li').filter({ hasText: 'Space Base' }).first()
    await result.waitFor({ timeout: 60000 })
    await result.click()

    await expect(page.locator('.detail-head h2')).toContainText('Space Base', { timeout: 10000 })
    await expect(page.getByRole('button', { name: /要約する|要約完了！/ })).toBeVisible()
  })
})

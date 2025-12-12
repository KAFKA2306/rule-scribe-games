import { test, expect } from '@playwright/test'

test.describe('Game List Loading', () => {
  test('should load games successfully on initial page load', async ({ page }) => {
    let apiResponseStatus = 0
    let apiResponseBody = null


    page.on('response', async (response) => {
      if (response.url().includes('/api/games') && response.request().method() === 'GET') {
        apiResponseStatus = response.status()
          apiResponseBody = await response.json()
      }
    })

    await page.goto('https://rule-scribe-games.vercel.app')

    await page.goto('https://rule-scribe-games.vercel.app')
    apiResponseStatus = gamesResponse.status()
      apiResponseBody = await gamesResponse.json()

    expect(apiResponseStatus).not.toBe(0)

    if (apiResponseStatus !== 200) {
      console.error(`API /api/games failed with status: ${apiResponseStatus}`)
      console.error('API Response Body:', apiResponseBody)
    }

    expect(apiResponseStatus).toBe(200)

    expect(Array.isArray(apiResponseBody)).toBe(true)

    if (apiResponseStatus === 200) {
      const errorMessage = page.locator(
        '.error-banner:has-text("ゲームの読み込みに失敗しました。")'
      )
      await expect(errorMessage).not.toBeVisible()

      const gameListHeader = page.locator('.game-list-pane h2')
      await expect(gameListHeader).toBeVisible()
    }
  })
})

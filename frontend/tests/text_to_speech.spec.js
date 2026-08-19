import { test, expect } from '@playwright/test'

async function stubSpeech(page) {
  await page.addInitScript(() => {
    class FakeSpeechSynthesisUtterance {
      constructor(text) {
        this.text = text
      }
    }

    Object.defineProperty(window, 'SpeechSynthesisUtterance', {
      configurable: true,
      value: FakeSpeechSynthesisUtterance,
    })
    Object.defineProperty(window, 'speechSynthesis', {
      configurable: true,
      value: {
        speak(utterance) {
          window.__lastUtterance = utterance
        },
        cancel() {
          window.__speechCancelCount = (window.__speechCancelCount || 0) + 1
        },
      },
    })
  })

  await page.route('**/api/games/game-one', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: '11111111-1111-4111-8111-111111111111',
        slug: 'game-one',
        title: 'Game One',
        title_ja: 'ゲーム1',
        summary: 'ゲームの要点です。',
        rules_content: '詳細ルール',
        structured_data: {},
      }),
    })
  })
}

test('GamePage speech state follows utterance lifecycle', async ({ page }) => {
  await stubSpeech(page)
  await page.goto('/games/game-one')

  const button = page.locator('.header-actions button[aria-pressed]')
  await expect(button).toHaveAccessibleName('ページの要点を読み上げ')
  await button.click()

  await expect(button).toHaveAccessibleName('要点の読み上げを停止')
  await expect(button).toHaveAttribute('aria-pressed', 'true')
  await expect(button).not.toHaveClass(/speaking/)

  await page.evaluate(() => window.__lastUtterance.onstart())
  await expect(button).toHaveClass(/speaking/)

  await page.evaluate(() => window.__lastUtterance.onend())
  await expect(button).toHaveAccessibleName('ページの要点を読み上げ')
  await expect(button).toHaveAttribute('aria-pressed', 'false')
  await expect(button).not.toHaveClass(/speaking/)
})

test('speech error returns the control to idle', async ({ page }) => {
  await stubSpeech(page)
  await page.goto('/games/game-one')

  const button = page.locator('.header-actions button[aria-pressed]')
  await button.click()
  await page.evaluate(() => window.__lastUtterance.onstart())
  await expect(button).toHaveClass(/speaking/)

  await page.evaluate(() => window.__lastUtterance.onerror(new Event('error')))
  await expect(button).toHaveAccessibleName('ページの要点を読み上げ')
  await expect(button).toHaveAttribute('aria-pressed', 'false')
  await expect(button).not.toHaveClass(/speaking/)
})

test('user stop cancels queued speech and returns the control to idle', async ({ page }) => {
  await stubSpeech(page)
  await page.goto('/games/game-one')

  const button = page.locator('.header-actions button[aria-pressed]')
  await button.click()
  await expect(button).toHaveAccessibleName('要点の読み上げを停止')

  await button.click()
  await expect(button).toHaveAccessibleName('ページの要点を読み上げ')
  await expect(button).toHaveAttribute('aria-pressed', 'false')
  await expect.poll(() => page.evaluate(() => window.__speechCancelCount || 0)).toBe(1)
})

test('leaving GamePage cancels active speech', async ({ page }) => {
  await stubSpeech(page)
  await page.goto('/games/game-one')

  const button = page.locator('.header-actions button[aria-pressed]')
  await button.click()
  await page.evaluate(() => window.__lastUtterance.onstart())
  await expect(button).toHaveClass(/speaking/)

  await page.getByRole('link', { name: '← DIRECTORY' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect.poll(() => page.evaluate(() => window.__speechCancelCount || 0)).toBe(1)
})

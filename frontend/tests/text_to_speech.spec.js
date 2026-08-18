import { test, expect } from '@playwright/test'

test('GamePage speech state follows utterance lifecycle', async ({ page }) => {
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
          window.__speechCancelled = true
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

  await page.goto('/games/game-one')

  const button = page.getByRole('button', { name: 'ページの要点を読み上げ' })
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

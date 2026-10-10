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
        setup_summary: 'カードを配ります。',
        gameplay_summary: '順番に手番を行います。',
        end_game_summary: '条件を満たしたら終了です。',
        rules_content: '詳細ルール本文です。',
        identity_status: 'verified',
        source_trust: 'official_publisher',
        content_review_status: 'human_reviewed',
        structured_data: {},
      }),
    })
  })
}

async function speechCancelCount(page) {
  return page.evaluate(() => window.__speechCancelCount || 0)
}

async function lastUtteranceText(page) {
  return page.evaluate(() => window.__lastUtterance?.text || '')
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

test('narration follows visible coach content and trust state', async ({ page }) => {
  await stubSpeech(page)
  await page.goto('/games/game-one')

  await expect(page.getByText('カードを配ります。')).toBeVisible()
  await page.locator('.header-actions button[aria-pressed]').click()

  const text = await lastUtteranceText(page)
  expect(text).toContain('ゲーム1')
  expect(text).toContain('カードを配ります。')
  expect(text).toContain('順番に手番を行います。')
  expect(text).toContain('条件を満たしたら終了です。')
  expect(text).toContain('IDENTITY VERIFIED')
  expect(text).toContain('PUBLISHER SOURCE')
  expect(text).toContain('HUMAN REVIEWED')
  expect(text).not.toContain('詳細ルール本文です。')
  expect(text).not.toContain('ゲームの要点です。')
})

test('rules view keeps narration scoped to the visible synopsis instead of full rules', async ({ page }) => {
  await stubSpeech(page)
  await page.goto('/games/game-one')

  await page.getByRole('button', { name: '詳しいルール' }).click()
  await expect(page.getByText('詳細ルール本文です。')).toBeVisible()
  await page.locator('.header-actions button[aria-pressed]').click()

  const text = await lastUtteranceText(page)
  expect(text).toContain('ゲーム1')
  expect(text).toContain('ゲームの要点です。')
  expect(text).toContain('PUBLISHER SOURCE')
  expect(text).toContain('HUMAN REVIEWED')
  expect(text).not.toContain('詳細ルール本文です。')
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
  const cancelCountBeforeSpeech = await speechCancelCount(page)
  await button.click()
  await expect(button).toHaveAccessibleName('要点の読み上げを停止')

  await button.click()
  await expect(button).toHaveAccessibleName('ページの要点を読み上げ')
  await expect(button).toHaveAttribute('aria-pressed', 'false')
  await expect.poll(() => speechCancelCount(page)).toBeGreaterThan(cancelCountBeforeSpeech)
})

test('leaving GamePage cancels active speech', async ({ page }) => {
  await stubSpeech(page)
  await page.goto('/games/game-one')

  const button = page.locator('.header-actions button[aria-pressed]')
  const cancelCountBeforeSpeech = await speechCancelCount(page)
  await button.click()
  await page.evaluate(() => window.__lastUtterance.onstart())
  await expect(button).toHaveClass(/speaking/)

  await page.getByRole('link', { name: '← DIRECTORY' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect.poll(() => speechCancelCount(page)).toBeGreaterThan(cancelCountBeforeSpeech)
})

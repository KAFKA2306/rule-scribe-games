import { test, expect } from '@playwright/test'

const games = [
  {
    id: '11111111-1111-4111-8111-111111111111',
    slug: 'palette-audit',
    title: 'Palette Audit',
    title_ja: '配色監査',
    summary: '配色回帰監査用ゲーム',
    description: '配色回帰監査用ゲーム',
    rules_content: '## 目的\n最後まで残る。',
    setup_summary: 'カードを配る。',
    gameplay_summary: '手番を順番に行う。',
    end_game_summary: '終了条件を満たしたら終了。',
    min_players: 2,
    max_players: 4,
    play_time: 30,
    min_age: 10,
    published_year: 2026,
    official_url: 'https://example.com/rules',
    structured_data: {
      mechanics: ['Bluffing', 'Roles'],
      keywords: [
        { term: 'ブラフ', description: '主張を読み合う' },
        { term: '役職', description: '固有能力を持つ' },
      ],
      pro_tips: [],
      rule_mistakes: [],
      persona_reviews: [],
      strategy_analysis: null,
    },
  },
  {
    id: '22222222-2222-4222-8222-222222222222',
    slug: 'palette-second',
    title: 'Palette Second',
    title_ja: '配色監査2',
    summary: '比較トレイ監査用ゲーム',
    min_players: 2,
    max_players: 5,
    play_time: 45,
    published_year: 2025,
    structured_data: { mechanics: ['Different Mechanic'] },
  },
]

async function mockApi(page) {
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname

    if (path === '/api/games' && request.method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ games, total: games.length }),
      })
      return
    }

    const match = path.match(/^\/api\/games\/([^/]+)$/)
    if (match && request.method() === 'GET') {
      const game = games.find((candidate) => candidate.slug === decodeURIComponent(match[1]))
      await route.fulfill({
        status: game ? 200 : 404,
        contentType: 'application/json',
        body: JSON.stringify(game || { detail: 'not found' }),
      })
      return
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })
}

function channelToLinear(channel) {
  const normalized = channel <= 1 ? channel : channel / 255
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4
}

function relativeLuminance([r, g, b]) {
  return (0.2126 * channelToLinear(r)) + (0.7152 * channelToLinear(g)) + (0.0722 * channelToLinear(b))
}

function parseColor(value) {
  const rgb = value.match(/rgba?\(([^)]+)\)/)
  if (rgb) {
    return rgb[1].split(/[ ,/]+/).filter(Boolean).slice(0, 3).map(Number)
  }

  const srgb = value.match(/color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)/)
  if (srgb) return srgb.slice(1, 4).map(Number)

  throw new Error(`Unsupported computed color: ${value}`)
}

async function expectLightSurface(locator, label) {
  await expect(locator, `${label} should be visible`).toBeVisible()
  const colors = await locator.evaluate((element) => {
    const style = getComputedStyle(element)
    return { background: style.backgroundColor, color: style.color }
  })
  const backgroundLum = relativeLuminance(parseColor(colors.background))
  const textLum = relativeLuminance(parseColor(colors.color))
  const contrast = (Math.max(backgroundLum, textLum) + 0.05) / (Math.min(backgroundLum, textLum) + 0.05)

  expect(backgroundLum, `${label} background ${colors.background} must stay in the light palette`).toBeGreaterThan(0.65)
  expect(contrast, `${label} contrast ${contrast.toFixed(2)} must remain readable`).toBeGreaterThanOrEqual(4.5)
}

test('every game-detail tab avoids legacy dark surfaces', async ({ page }, testInfo) => {
  await mockApi(page)
  await page.goto('/games/palette-audit')
  await expect(page.getByRole('heading', { name: '配色監査' })).toBeVisible()

  await page.getByRole('tab', { name: /セットアップ/ }).click()
  const coachSteps = page.locator('.coach-step')
  await expect(coachSteps).toHaveCount(3)
  for (let index = 0; index < 3; index += 1) {
    await expectLightSurface(coachSteps.nth(index), `coach step ${index + 1}`)
  }

  await page.getByRole('tab', { name: /戦略/ }).click()
  await expectLightSurface(page.locator('.game-empty-state'), 'strategy empty state')

  await page.getByRole('tab', { name: /レビュー/ }).click()
  await expectLightSurface(page.locator('.game-empty-state'), 'review empty state')
  await page.screenshot({ path: testInfo.outputPath('review-light-state.png'), fullPage: true, animations: 'disabled' })

  await page.getByRole('tab', { name: /関連ゲーム/ }).click()
  await expect(page.getByText('関連ゲームはまだ見つかっていません。').first()).toBeVisible()

  const legacyDark = await page.locator('.game-detail-content').evaluate((root) => {
    const visible = [...root.querySelectorAll('*')].filter((element) => {
      const rect = element.getBoundingClientRect()
      const style = getComputedStyle(element)
      return rect.width >= 80 && rect.height >= 40 && style.visibility !== 'hidden' && style.display !== 'none'
    })
    return visible
      .map((element) => ({
        tag: element.tagName,
        className: element.className?.toString?.() || '',
        background: getComputedStyle(element).backgroundColor,
      }))
      .filter(({ background }) => background === 'rgb(17, 17, 17)' || background === 'rgb(26, 26, 26)' || background === 'rgb(10, 10, 10)')
  })
  expect(legacyDark, JSON.stringify(legacyDark, null, 2)).toEqual([])
})

test('directory empty state and comparison tray use the same light palette', async ({ page }, testInfo) => {
  await mockApi(page)
  await page.goto('/')
  await expect(page.getByText('配色監査', { exact: true })).toBeVisible()

  const compareButtons = page.getByRole('button', { name: 'COMPARE' })
  await compareButtons.nth(0).click()
  await compareButtons.nth(1).click()
  await expectLightSurface(page.locator('.comparison-tray'), 'comparison tray')

  const search = page.getByPlaceholder('ゲームを検索、または未登録ゲームをAI生成...')
  await search.fill('no-match-palette-audit')
  await expect(page.getByText('条件に一致するゲームが見つかりません。')).toBeVisible()
  await expectLightSurface(page.locator('.app-empty-state'), 'directory empty state')
  await page.screenshot({ path: testInfo.outputPath('directory-light-empty-state.png'), fullPage: true, animations: 'disabled' })
})

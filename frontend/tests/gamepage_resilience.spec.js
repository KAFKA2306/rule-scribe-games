import { test, expect } from '@playwright/test'

const productionBaseURL = globalThis.process?.env?.PLAYWRIGHT_BASE_URL

const fixtureGame = {
  id: 'resilience-fixture-id',
  slug: 'resilience-fixture',
  title: 'Resilience fixture',
  title_ja: '保持テスト',
  summary: '取得済みの概要はAPI失敗後も表示されます。',
  description: '取得済みの概要はAPI失敗後も表示されます。',
  min_players: 2,
  max_players: 2,
  play_time: 30,
  play_time_min_minutes: 30,
  play_time_max_minutes: 30,
  identity_status: 'verified',
  source_trust: 'official_publisher',
  content_review_status: 'human_reviewed',
  rules_content: '## Setup\n- Each player begins with a retained rule from the initial HTML.',
}

function ssrArticle(game) {
  return `<article itemscope itemtype="https://schema.org/Game" data-ssr-game="true">
    <h1 itemprop="name">${game.title_ja}</h1>
    <p itemprop="description">${game.summary}</p>
    <pre itemprop="text">${game.rules_content}</pre>
  </article>`
}

function ssrPayloadScript(game) {
  const safeJson = JSON.stringify(game)
    .replaceAll('<', '\\u003c')
    .replaceAll('>', '\\u003e')
    .replaceAll('&', '\\u0026')
  return `<script type="application/json" id="ssr-game-data">${safeJson}</script>`
}

test('keeps SSR game rules visible when the detail API fails after client takeover', async ({
  page,
}) => {
  const shellResponse = await page.request.get('/')
  const shell = await shellResponse.text()
  const ssrHtml = shell
    .replace('</head>', `${ssrPayloadScript(fixtureGame)}</head>`)
    .replace('<div id="root"></div>', `<div id="root">${ssrArticle(fixtureGame)}</div>`)

  await page.route('**/games/resilience-fixture', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: ssrHtml,
    })
  )
  await page.route('**/api/games/resilience-fixture', (route) => route.abort())
  await page.route('**/api/games/resilience-fixture/*', (route) =>
    route.fulfill({ status: 404, contentType: 'application/json', body: '{"detail":"not found"}' })
  )

  await page.goto('/games/resilience-fixture')

  await expect(page.getByRole('heading', { name: '保持テスト' })).toBeVisible()
  await expect(page.getByText('取得済みの概要はAPI失敗後も表示されます。')).toBeVisible()
  await expect(
    page.getByText('Each player begins with a retained rule from the initial HTML.')
  ).toBeVisible()
  await expect(page.locator('.game-page-notice')).toContainText(
    '取得済みのゲーム情報を表示しています'
  )
  await expect(page.getByRole('button', { name: '再試行' })).toBeVisible()
})

test('production Brass Birmingham rules remain readable if the detail API is aborted', async ({
  page,
}) => {
  test.skip(!productionBaseURL, 'production SSR acceptance is checked against the deployed site')

  const htmlResponse = await page.request.get('/games/brass-birmingham')
  expect(htmlResponse.ok()).toBe(true)
  const html = await htmlResponse.text()
  const payloadMatch = html.match(
    /<script type="application\/json" id="ssr-game-data">(.*?)<\/script>/s
  )
  expect(payloadMatch).not.toBeNull()
  const initialGame = JSON.parse(payloadMatch[1])
  expect(initialGame.slug).toBe('brass-birmingham')
  expect(initialGame.rules_content).toBeTruthy()
  const firstRule = initialGame.rules_content
    .split('\n')
    .find((line) => line.trim() && !line.trim().startsWith('#'))
    ?.replace(/^\s*[-*]\s*/, '')
    .slice(0, 50)
  expect(firstRule).toBeTruthy()

  await page.goto('/games/brass-birmingham')
  await expect(
    page.getByRole('heading', { name: initialGame.title_ja || initialGame.title })
  ).toBeVisible()
  await expect(page.getByText(firstRule, { exact: false }).first()).toBeVisible()

  await page.route('**/api/games/brass-birmingham', (route) => route.abort())
  await page.goto('/games/brass-birmingham')
  await expect(
    page.getByRole('heading', { name: initialGame.title_ja || initialGame.title })
  ).toBeVisible()
  await expect(page.getByText(firstRule, { exact: false }).first()).toBeVisible()
  await expect(page.locator('.game-page-notice')).toContainText(
    '取得済みのゲーム情報を表示しています'
  )
})

import { test, expect } from '@playwright/test'

const USER_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const LIST_ID = 'aaaaaaaa-0000-4000-8000-000000000111'
const GAME_ONE_ID = '11111111-1111-4111-8111-111111111111'
const GAME_TWO_ID = '22222222-2222-4222-8222-222222222222'
const TOKEN = 'eyJhbGciOiJub25lIn0.eyJzdWIiOiJhYWFhYWFhYS1hYWFhLTRhYWEtOGFhYS1hYWFhYWFhYWFhYWFhYSIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjo0MTAyNDQ0ODAwfQ.'

const games = [
  {
    id: GAME_ONE_ID,
    slug: 'game-one',
    title: 'Game One',
    title_ja: 'ゲーム1',
    summary: '最初のテストゲーム',
    min_players: 2,
    max_players: 4,
    play_time: 45,
    published_year: 2026,
    structured_data: {},
  },
  {
    id: GAME_TWO_ID,
    slug: 'game-two',
    title: 'Game Two',
    title_ja: 'ゲーム2',
    summary: '2番目のテストゲーム',
    min_players: 2,
    max_players: 5,
    play_time: 60,
    published_year: 2026,
    structured_data: {},
  },
]

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function installSession(page) {
  await page.addInitScript(({ token, userId }) => {
    localStorage.setItem('sb-example-auth-token', JSON.stringify({
      access_token: token,
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: 4102444800,
      refresh_token: 'test-refresh',
      user: {
        id: userId,
        aud: 'authenticated',
        role: 'authenticated',
        email: 'user@example.com',
        user_metadata: { full_name: 'Test User' },
      },
    }))
  }, { token: TOKEN, userId: USER_ID })
}

async function installRuntimeAudit(page) {
  const consoleErrors = []
  const pageErrors = []
  const failedRequests = []
  const failedResponses = []

  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })
  page.on('pageerror', (error) => pageErrors.push(error.message))
  page.on('requestfailed', (request) => {
    const url = new URL(request.url())
    if (url.pathname.startsWith('/api/')) failedRequests.push(`${request.method()} ${url.pathname}: ${request.failure()?.errorText || 'failed'}`)
  })
  page.on('response', (response) => {
    const url = new URL(response.url())
    if (url.pathname.startsWith('/api/') && response.status() >= 400) {
      failedResponses.push(`${response.request().method()} ${url.pathname}: ${response.status()}`)
    }
  })

  await page.addInitScript(() => {
    window.__uiUxUnhandledRejections = []
    window.__uiUxCls = 0
    window.addEventListener('unhandledrejection', (event) => {
      const reason = event.reason
      window.__uiUxUnhandledRejections.push(String(reason?.message || reason || 'unknown rejection'))
    })
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) window.__uiUxCls += entry.value
        }
      }).observe({ type: 'layout-shift', buffered: true })
    } catch {
      // LayoutShift is not available in every browser build; Chromium CI supports it.
    }
  })

  return async () => {
    const browserAudit = await page.evaluate(() => ({
      rejections: window.__uiUxUnhandledRejections || [],
      cls: window.__uiUxCls || 0,
    }))
    expect(consoleErrors, `console errors: ${consoleErrors.join('\n')}`).toEqual([])
    expect(pageErrors, `page errors: ${pageErrors.join('\n')}`).toEqual([])
    expect(failedRequests, `failed critical requests: ${failedRequests.join('\n')}`).toEqual([])
    expect(failedResponses, `failed critical responses: ${failedResponses.join('\n')}`).toEqual([])
    expect(browserAudit.rejections, `unhandled rejections: ${browserAudit.rejections.join('\n')}`).toEqual([])
    return browserAudit
  }
}

function createApiState() {
  return {
    customLists: [],
    details: new Map(),
    itemCounter: 0,
  }
}

function listItem(state, game) {
  state.itemCounter += 1
  return {
    id: `aaaaaaaa-1000-4000-8000-${String(state.itemCounter).padStart(12, '0')}`,
    list_id: LIST_ID,
    game_id: game.id,
    game_title_snapshot: game.title_ja,
    position: state.itemCounter - 1,
    created_at: '2026-08-14T03:00:00Z',
    updated_at: '2026-08-14T03:00:00Z',
    unavailable: false,
    game: {
      id: game.id,
      slug: game.slug,
      title: game.title,
      title_ja: game.title_ja,
      image_url: null,
    },
  }
}

async function mockApi(page, state) {
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname
    const method = request.method()

    if (path === '/api/games' && method === 'GET') {
      await delay(120)
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games, total: games.length }) })
      return
    }

    const gameMatch = path.match(/^\/api\/games\/([^/]+)$/)
    if (gameMatch && method === 'GET') {
      await delay(100)
      const game = games.find((candidate) => candidate.slug === decodeURIComponent(gameMatch[1]))
      await route.fulfill({ status: game ? 200 : 404, contentType: 'application/json', body: JSON.stringify(game || { detail: 'not found' }) })
      return
    }

    const glossaryMatch = path.match(/^\/api\/games\/([^/]+)\/glossary$/)
    if (glossaryMatch && method === 'GET') {
      const game = games.find((candidate) => candidate.slug === decodeURIComponent(glossaryMatch[1]))
      await route.fulfill({
        status: game ? 200 : 404,
        contentType: 'application/json',
        body: JSON.stringify(game ? { status: 'not_available', entries: [] } : { detail: 'not found' }),
      })
      return
    }

    if (path === '/api/lists') {
      if (method === 'GET') {
        await delay(120)
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ lists: state.customLists }) })
        return
      }
      if (method === 'POST') {
        await delay(120)
        const body = request.postDataJSON()
        const created = { id: LIST_ID, owner_id: USER_ID, name: body.name, visibility: 'private', system_key: null }
        state.customLists = [created]
        state.details.set(LIST_ID, { ...created, items: [] })
        await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(created) })
        return
      }
    }

    if (path === '/api/owned-games' && method === 'GET') {
      await delay(120)
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: null, owner_id: USER_ID, name: '所持ゲーム', visibility: 'private', system_key: 'owned', items: [] }),
      })
      return
    }

    const ownedStatusMatch = path.match(/^\/api\/owned-games\/([0-9a-f-]+)$/)
    if (ownedStatusMatch && method === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ owned: false, item_id: null, created_at: null }) })
      return
    }

    const listMatch = path.match(/^\/api\/lists\/([0-9a-f-]+)$/)
    if (listMatch) {
      const listId = listMatch[1]
      if (method === 'GET') {
        await delay(120)
        const detail = state.details.get(listId)
        await route.fulfill({ status: detail ? 200 : 404, contentType: 'application/json', body: JSON.stringify(detail || { detail: 'not found' }) })
        return
      }
      if (method === 'DELETE') {
        await delay(100)
        state.customLists = state.customLists.filter((list) => list.id !== listId)
        state.details.delete(listId)
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'deleted' }) })
        return
      }
    }

    const addItemMatch = path.match(/^\/api\/lists\/([0-9a-f-]+)\/items$/)
    if (addItemMatch && method === 'POST') {
      await delay(120)
      const listId = addItemMatch[1]
      const detail = state.details.get(listId)
      const body = request.postDataJSON()
      const game = games.find((candidate) => candidate.id === body.game_id)
      const item = listItem(state, game)
      detail.items.push(item)
      detail.items.forEach((candidate, index) => { candidate.position = index })
      await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(item) })
      return
    }

    const removeItemMatch = path.match(/^\/api\/lists\/([0-9a-f-]+)\/items\/([0-9a-f-]+)$/)
    if (removeItemMatch && method === 'DELETE') {
      await delay(100)
      const detail = state.details.get(removeItemMatch[1])
      detail.items = detail.items.filter((item) => item.id !== removeItemMatch[2])
      detail.items.forEach((candidate, index) => { candidate.position = index })
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'deleted' }) })
      return
    }

    const reorderMatch = path.match(/^\/api\/lists\/([0-9a-f-]+)\/order$/)
    if (reorderMatch && method === 'PUT') {
      await delay(120)
      const detail = state.details.get(reorderMatch[1])
      const body = request.postDataJSON()
      const byId = new Map(detail.items.map((item) => [item.id, item]))
      detail.items = body.item_ids.map((id, index) => ({ ...byId.get(id), position: index }))
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'reordered' }) })
      return
    }

    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: `unmocked ${method} ${path}` }) })
  })
}

async function assertViewportSafe(page) {
  const layout = await page.evaluate(() => {
    const viewport = document.documentElement.clientWidth
    const boxes = [...document.querySelectorAll('header, main, aside, [data-auth-control], .lists-item')]
      .map((node) => node.getBoundingClientRect())
      .filter((box) => box.width > 0 && box.height > 0)
      .map((box) => ({ left: box.left, right: box.right }))
    return { viewport, scrollWidth: document.documentElement.scrollWidth, boxes }
  })
  expect(layout.scrollWidth).toBeLessThanOrEqual(layout.viewport + 1)
  for (const box of layout.boxes) {
    expect(box.left).toBeGreaterThanOrEqual(-1)
    expect(box.right).toBeLessThanOrEqual(layout.viewport + 1)
  }
}

test('anonymous directory -> game detail stays error-free and SPA-local', async ({ page }) => {
  const state = createApiState()
  await mockApi(page, state)
  const finishAudit = await installRuntimeAudit(page)

  await page.goto('/')
  await expect(page.getByText('ゲーム1', { exact: true }).first()).toBeVisible()
  await assertViewportSafe(page)

  await page.evaluate(() => { window.__uiUxDocumentMarker = 'alive' })
  await page.getByRole('link', { name: /ゲーム1/ }).first().click()
  await expect(page).toHaveURL(/\/games\/game-one$/)
  await expect.poll(() => page.evaluate(() => document.activeElement?.matches('main, .game-detail-content'))).toBe(true)
  expect(await page.evaluate(() => window.__uiUxDocumentMarker)).toBe('alive')
  expect(await page.evaluate(() => performance.getEntriesByType('navigation').length)).toBe(1)
  await assertViewportSafe(page)

  const audit = await finishAudit()
  expect(audit.cls).toBeLessThan(0.1)
})

test('authenticated list lifecycle survives navigation, reload, reorder, and destructive actions', async ({ page }, testInfo) => {
  await installSession(page)
  const state = createApiState()
  await mockApi(page, state)
  const finishAudit = await installRuntimeAudit(page)

  await page.goto('/lists')
  await expect(page.getByRole('heading', { name: '所持ゲーム' })).toBeVisible()
  await assertViewportSafe(page)
  expect((await finishAudit()).cls).toBeLessThan(0.1)

  await page.getByLabel('新しいリスト名').fill('E2E コレクション')
  await page.getByRole('button', { name: 'リストを作成' }).click()
  await expect(page.getByRole('button', { name: 'E2E コレクション' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'E2E コレクション' })).toBeVisible()

  await page.evaluate(() => { window.__uiUxDocumentMarker = 'alive' })
  await page.getByRole('link', { name: '← DIRECTORY' }).click()
  await expect(page.getByText('ゲーム1', { exact: true }).first()).toBeVisible()
  await page.getByRole('link', { name: /ゲーム1/ }).first().click()
  await expect(page).toHaveURL(/\/games\/game-one$/)
  expect(await page.evaluate(() => window.__uiUxDocumentMarker)).toBe('alive')

  await page.getByRole('button', { name: 'リストに保存' }).click()
  await expect(page.getByText('保存しました', { exact: true })).toBeVisible()
  await page.goBack()
  await expect(page.getByText('ゲーム2', { exact: true }).first()).toBeVisible()
  await page.getByRole('link', { name: /ゲーム2/ }).first().click()
  await expect(page).toHaveURL(/\/games\/game-two$/)
  expect(await page.evaluate(() => window.__uiUxDocumentMarker)).toBe('alive')

  await page.getByRole('button', { name: 'リストに保存' }).click()
  await expect(page.getByText('保存しました', { exact: true })).toBeVisible()
  await page.getByRole('link', { name: '一覧で確認' }).click()
  await expect(page).toHaveURL(new RegExp(`/lists\\?list=${LIST_ID}`))
  await expect(page.locator('.lists-item')).toHaveCount(2)
  expect(await page.evaluate(() => window.__uiUxDocumentMarker)).toBe('alive')
  expect(await page.evaluate(() => performance.getEntriesByType('navigation').length)).toBe(1)
  await assertViewportSafe(page)
  await page.screenshot({ path: testInfo.outputPath('lists-two-items.png'), fullPage: true, animations: 'disabled' })

  await page.goBack()
  await expect(page).toHaveURL(/\/games\/game-two$/)
  await page.goForward()
  await expect(page).toHaveURL(new RegExp(`/lists\\?list=${LIST_ID}`))
  await expect(page.locator('.lists-item')).toHaveCount(2)

  await page.getByRole('button', { name: 'ゲーム2を上へ' }).click()
  await expect(page.locator('.lists-item__title').first()).toHaveText('ゲーム2')
  await expect(page.getByText('変更を反映しています…')).toBeVisible()
  await expect(page.getByText('変更を反映しています…')).toHaveCount(0)

  await page.reload()
  await expect(page.locator('.lists-item')).toHaveCount(2)
  await expect(page.locator('.lists-item__title').first()).toHaveText('ゲーム2')
  await assertViewportSafe(page)

  await page.getByRole('button', { name: 'リストから削除' }).first().click()
  await expect(page.locator('.lists-item')).toHaveCount(1)

  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'リストを削除' }).click()
  await expect(page.getByRole('heading', { name: '所持ゲーム' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'E2E コレクション' })).toHaveCount(0)
  await assertViewportSafe(page)

  const audit = await finishAudit()
  expect(audit.cls).toBeLessThan(0.1)
})

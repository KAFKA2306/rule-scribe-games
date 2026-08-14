import { test, expect } from '@playwright/test'

const USER_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const LIST_ID = 'aaaaaaaa-0000-4000-8000-000000000001'
const TOKEN = 'eyJhbGciOiJub25lIn0.eyJzdWIiOiJhYWFhYWFhYS1hYWFhLTRhYWEtOGFhYS1hYWFhYWFhYWFhYWFhYSIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjo0MTAyNDQ0ODAwfQ.'
const LONG_TITLE = 'これは非常に長い日本語タイトルと Extremely Long English Board Game Title That Must Wrap Without Colliding With Any Action Controls です'

function item(index, overrides = {}) {
  const gameId = `11111111-1111-4111-8111-${String(index + 1).padStart(12, '0')}`
  return {
    id: `aaaaaaaa-1000-4000-8000-${String(index + 1).padStart(12, '0')}`,
    game_id: gameId,
    game_title_snapshot: `ゲーム${index + 1}`,
    position: index,
    created_at: '2026-08-14T01:34:48Z',
    unavailable: false,
    game: {
      id: gameId,
      slug: `game-${index + 1}`,
      title: `Game ${index + 1}`,
      title_ja: index === 0 ? LONG_TITLE : `ゲーム${index + 1}`,
    },
    ...overrides,
  }
}

const MANY_ITEMS = [
  item(0),
  item(1, { game_id: null, game: null, unavailable: true, game_title_snapshot: '現在利用できない長いゲームタイトル / Unavailable Archived Board Game Edition' }),
  ...Array.from({ length: 10 }, (_, index) => item(index + 2)),
]

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

async function mockLists(page, getItems = () => MANY_ITEMS) {
  await page.route('**/api/lists', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        lists: [{ id: LIST_ID, name: 'Favorites / 長い名前のマイリスト', visibility: 'private', system_key: null }],
      }),
    })
  })
  await page.route(`**/api/lists/${LIST_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: LIST_ID,
        name: 'Favorites / 長い名前のマイリスト',
        visibility: 'private',
        system_key: null,
        items: getItems(),
      }),
    })
  })
  await page.route('**/api/owned-games', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: null, name: '所持ゲーム', visibility: 'private', system_key: 'owned', items: [] }),
    })
  })
}

async function readLayout(page) {
  return page.evaluate(() => {
    const viewport = document.documentElement.clientWidth
    const pageEl = document.querySelector('.lists-page')?.getBoundingClientRect()
    const shell = document.querySelector('.lists-shell')?.getBoundingClientRect()
    const header = document.querySelector('.lists-header')?.getBoundingClientRect()
    const auth = document.querySelector('[data-auth-control]')?.getBoundingClientRect()
    const itemRects = [...document.querySelectorAll('.lists-item')].map((node) => {
      const item = node.getBoundingClientRect()
      const content = node.querySelector('.lists-item__content')?.getBoundingClientRect()
      const actions = node.querySelector('.lists-item__actions')?.getBoundingClientRect()
      return {
        item: { left: item.left, right: item.right, top: item.top, bottom: item.bottom, width: item.width },
        content: content ? { left: content.left, right: content.right, top: content.top, bottom: content.bottom } : null,
        actions: actions ? { left: actions.left, right: actions.right, top: actions.top, bottom: actions.bottom } : null,
      }
    })
    if (!pageEl || !shell || !header || !auth) throw new Error('lists layout nodes are missing')
    return {
      viewport,
      scrollWidth: document.documentElement.scrollWidth,
      page: { left: pageEl.left, right: pageEl.right, width: pageEl.width },
      shell: { left: shell.left, right: shell.right, width: shell.width },
      header: { left: header.left, right: header.right, top: header.top, bottom: header.bottom },
      auth: { left: auth.left, right: auth.right, top: auth.top, bottom: auth.bottom },
      itemRects,
    }
  })
}

for (const viewport of [
  { width: 320, height: 800 },
  { width: 375, height: 812 },
  { width: 768, height: 1024 },
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  test(`lists layout stays inside ${viewport.width}px viewport`, async ({ page }) => {
    await installSession(page)
    await mockLists(page)
    await page.setViewportSize(viewport)
    await page.goto(`/lists?list=${LIST_ID}`)
    await expect(page.getByRole('heading', { name: 'Favorites / 長い名前のマイリスト' })).toBeVisible()
    await expect(page.locator('.lists-item')).toHaveCount(12)

    const layout = await readLayout(page)
    expect(layout.scrollWidth).toBe(layout.viewport)
    expect(Math.abs(layout.page.left)).toBeLessThanOrEqual(1)
    expect(Math.abs(layout.page.width - layout.viewport)).toBeLessThanOrEqual(2)
    expect(layout.shell.left).toBeGreaterThanOrEqual(0)
    expect(layout.shell.right).toBeLessThanOrEqual(layout.viewport + 1)
    expect(Math.abs(layout.shell.left - (layout.viewport - layout.shell.width) / 2)).toBeLessThanOrEqual(2)
    expect(layout.auth.left).toBeGreaterThanOrEqual(layout.header.left - 1)
    expect(layout.auth.right).toBeLessThanOrEqual(layout.header.right + 1)

    if (viewport.width >= 1280) {
      expect(layout.shell.width).toBeGreaterThanOrEqual(1100)
    }

    for (const row of layout.itemRects) {
      expect(row.item.left).toBeGreaterThanOrEqual(-1)
      expect(row.item.right).toBeLessThanOrEqual(layout.viewport + 1)
      expect(row.actions?.right).toBeLessThanOrEqual(row.item.right + 1)
      if (viewport.width >= 641) {
        expect(row.content?.right).toBeLessThanOrEqual(row.actions.left + 1)
      } else {
        expect(row.actions?.top).toBeGreaterThanOrEqual(row.content.bottom - 1)
      }
    }
  })
}

test('0, 1, and 10+ item fixtures preserve hierarchy and unavailable state', async ({ page }) => {
  await installSession(page)
  let currentItems = []
  await mockLists(page, () => currentItems)
  await page.setViewportSize({ width: 1024, height: 768 })

  await page.goto(`/lists?list=${LIST_ID}`)
  await expect(page.getByText('このリストは空です。ゲーム詳細から追加できます。')).toBeVisible()
  await expect(page.locator('.lists-item')).toHaveCount(0)

  currentItems = [item(0)]
  await page.reload()
  await expect(page.locator('.lists-item')).toHaveCount(1)
  await expect(page.getByText(LONG_TITLE, { exact: true })).toBeVisible()

  currentItems = MANY_ITEMS
  await page.reload()
  await expect(page.locator('.lists-item')).toHaveCount(12)
  await expect(page.getByText('現在利用できないゲーム')).toBeVisible()
  await expect(page.getByRole('button', { name: 'リストを削除' })).toHaveClass(/lists-danger/)
  await expect(page.getByRole('button', { name: 'リストから削除' }).first()).toHaveClass(/lists-danger/)
})

for (const viewport of [
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'desktop-1440', width: 1440, height: 900 },
]) {
  test(`lists visual baseline ${viewport.name}`, async ({ page }) => {
    await installSession(page)
    await mockLists(page)
    await page.setViewportSize({ width: viewport.width, height: viewport.height })
    await page.goto(`/lists?list=${LIST_ID}`)
    await expect(page.locator('.lists-item')).toHaveCount(12)
    await expect(page).toHaveScreenshot(`lists-${viewport.name}.png`, {
      fullPage: true,
      animations: 'disabled',
      caret: 'hide',
      maxDiffPixelRatio: 0.002,
    })
  })
}

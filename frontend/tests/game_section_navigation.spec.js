import { test, expect } from '@playwright/test'

const game = {
  id: 76,
  slug: 'big-shot',
  title: 'Big Shot',
  title_ja: 'ビッグショット',
  min_players: 2,
  max_players: 4,
  play_time: 45,
  min_age: 10,
  published_year: 2001,
  summary: '土地を競り落とし、資金を管理しながら得点を競うオークションゲーム。',
  setup_summary: '各プレイヤーは開始時の資金を受け取ります。',
  gameplay_summary: '競りで土地を獲得し、資金配分を管理します。',
  end_game_summary: '全区画の競りが終わったら得点を計算します。',
  source_url: 'https://example.com/big-shot-source',
  source_trust: 'third_party',
  content_review_status: 'review_required',
  rules_content: '# Big Shot Rules\n\n## 準備\n\n開始資金を受け取ります。\n\n## ゲームの流れ\n\n競りを行い、土地を獲得します。\n\n## 得点\n\n獲得した土地から得点を計算します。\n\n## 2人プレイ\n\n2人用の条件を確認します。',
  structured_data: {
    strategy_analysis: '## Strategy\n\n資金効率を優先します。',
    persona_reviews: [{ persona: '慎重派', rating: 8, review_text: '資金管理が重要です。' }],
    keywords: [],
  },
}

async function mockGameApi(page, value = game) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === `/api/games/${value.slug}`) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: value }) })
      return
    }
    if (url.pathname === `/api/games/${value.slug}/connections`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'available', connections: [], algorithm_version: 'test' }),
      })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('GamePageのsection fragmentをdirect loadとBack/Forwardで復元する', async ({ page }) => {
  await mockGameApi(page)
  await page.goto('/games/big-shot#setup')

  const rules = page.getByRole('button', { name: '詳しいルール', exact: true })
  const setup = page.getByRole('button', { name: '準備・流れ・終了', exact: true })

  await expect(setup).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByText(game.setup_summary)).toBeVisible()

  await rules.click()
  await expect(page).toHaveURL(/#rules$/)
  await expect(rules).toHaveAttribute('aria-pressed', 'true')

  await setup.click()
  await expect(page).toHaveURL(/#setup$/)
  await expect(setup).toHaveAttribute('aria-pressed', 'true')

  await page.goBack()
  await expect(page).toHaveURL(/#rules$/)
  await expect(rules).toHaveAttribute('aria-pressed', 'true')

  await page.goForward()
  await expect(page).toHaveURL(/#setup$/)
  await expect(setup).toHaveAttribute('aria-pressed', 'true')
})

test('unknown fragmentと存在しないsectionは詳しいルールへ戻す', async ({ page }) => {
  const withoutOptionalSections = {
    ...game,
    slug: 'minimal-game',
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
    structured_data: {
      ...game.structured_data,
      strategy_analysis: null,
      persona_reviews: [],
    },
  }
  await mockGameApi(page, withoutOptionalSections)

  await page.goto('/games/minimal-game#strategy')
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('button', { name: '戦略', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'レビュー', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '準備・流れ・終了', exact: true })).toHaveCount(0)

  await page.goto('/games/minimal-game#obsolete')
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toHaveAttribute('aria-pressed', 'true')
})

test('connections fragmentから関連ゲーム取得を開始する', async ({ page }) => {
  let connectionRequests = 0
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/big-shot/connections') {
      connectionRequests += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'available', connections: [], algorithm_version: 'test' }),
      })
      return
    }
    if (url.pathname === '/api/games/big-shot') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/big-shot#connections')
  await expect(page.getByRole('button', { name: '関連ゲーム', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByText('正準Concept上の関連ゲームはまだ登録されていません。')).toBeVisible()
  expect(connectionRequests).toBe(1)
})

test('詳細ルール見出しへdirect loadでき、見出し一覧から同じfragmentへ移動できる', async ({ page }) => {
  await mockGameApi(page)
  await page.goto('/games/big-shot#rule-%E5%BE%97%E7%82%B9')

  const rules = page.getByRole('button', { name: '詳しいルール', exact: true })
  const scoreHeading = page.getByRole('heading', { name: '得点', exact: true })

  await expect(rules).toHaveAttribute('aria-pressed', 'true')
  await expect(scoreHeading).toHaveAttribute('id', 'rule-得点')
  await expect(scoreHeading).toBeFocused()

  await page.getByRole('link', { name: '2人プレイ', exact: true }).click()
  await expect(page).toHaveURL(/#rule-/)
  const twoPlayerHeading = page.getByRole('heading', { name: '2人プレイ', exact: true })
  await expect(twoPlayerHeading).toHaveAttribute('id', 'rule-2人プレイ')
  await expect(twoPlayerHeading).toBeFocused()
})

test('375pxでも詳細ルール見出しへ1回のsection link操作で移動できる', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 })
  await mockGameApi(page)
  await page.goto('/games/big-shot#rules')

  const sectionNav = page.getByRole('navigation', { name: 'ルール内の見出し' })
  await expect(sectionNav).toBeVisible()
  await sectionNav.getByRole('link', { name: 'ゲームの流れ', exact: true }).click()

  await expect(page.getByRole('heading', { name: 'ゲームの流れ', exact: true })).toBeFocused()
})

import { test, expect } from '@playwright/test'

const affiliateGame = {
  id: 9001,
  slug: 'affiliate-fixture',
  title: 'Affiliate Fixture',
  title_ja: 'アフィリエイト検証ゲーム',
  summary: '収益リンク計測の検証用ゲーム。',
  rules_content: '# Rules',
  structured_data: {},
  identity_status: 'verified',
  source_trust: 'official_publisher',
  content_review_status: 'human_reviewed',
  source_url: 'https://publisher.example/game',
  affiliate_urls: {
    amazon: 'https://www.amazon.co.jp/dp/example?tag=bodogemikata-22',
    rakuten: 'https://example.rakuten.co.jp/item/game',
  },
}

async function mockGame(page, game = affiliateGame) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === `/api/games/${game.slug}`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ game }),
      })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('affiliate click emits one aggregate-safe Web Analytics event and keeps sponsored relation', async ({ page }) => {
  await page.addInitScript(() => {
    window.__analyticsCalls = []
    window.va = (...args) => window.__analyticsCalls.push(args)
  })
  await mockGame(page)
  await page.goto('/games/affiliate-fixture')

  const amazon = page.getByRole('link', { name: 'Amazon', exact: true })
  await expect(amazon).toHaveAttribute('rel', 'noopener noreferrer sponsored')
  await amazon.evaluate(element => element.addEventListener('click', event => event.preventDefault(), { once: true }))
  await amazon.click()

  expect(await page.evaluate(() => window.__analyticsCalls)).toEqual([
    [
      'event',
      {
        name: 'Affiliate Outbound',
        data: { gameSlug: 'affiliate-fixture', provider: 'amazon' },
      },
    ],
  ])
})

test('legacy Amazon URL with an Associates tag is treated as sponsored and measured', async ({ page }) => {
  await page.addInitScript(() => {
    window.__analyticsCalls = []
    window.va = (...args) => window.__analyticsCalls.push(args)
  })
  const legacyTaggedAmazon = {
    ...affiliateGame,
    slug: 'legacy-amazon-fixture',
    affiliate_urls: null,
    amazon_url: 'https://www.amazon.co.jp/s?k=game&tag=bodogemikata-22',
  }
  await mockGame(page, legacyTaggedAmazon)
  await page.goto('/games/legacy-amazon-fixture')

  const amazon = page.getByRole('link', { name: 'Amazon', exact: true })
  await expect(amazon).toHaveAttribute('rel', 'noopener noreferrer sponsored')
  await amazon.evaluate(element => element.addEventListener('click', event => event.preventDefault(), { once: true }))
  await amazon.click()

  expect(await page.evaluate(() => window.__analyticsCalls)).toEqual([
    [
      'event',
      {
        name: 'Affiliate Outbound',
        data: { gameSlug: 'legacy-amazon-fixture', provider: 'amazon' },
      },
    ],
  ])
})

test('non-monetized outbound links do not emit affiliate events', async ({ page }) => {
  await page.addInitScript(() => {
    window.__analyticsCalls = []
    window.va = (...args) => window.__analyticsCalls.push(args)
  })
  const communityOnly = {
    ...affiliateGame,
    slug: 'community-fixture',
    affiliate_urls: null,
    amazon_url: null,
    bgg_url: 'https://boardgamegeek.com/boardgame/1/example',
  }
  await mockGame(page, communityOnly)
  await page.goto('/games/community-fixture')

  const bgg = page.getByRole('link', { name: 'BoardGameGeek', exact: true })
  await expect(bgg).toHaveAttribute('rel', 'noopener noreferrer')
  await bgg.evaluate(element => element.addEventListener('click', event => event.preventDefault(), { once: true }))
  await bgg.click()

  expect(await page.evaluate(() => window.__analyticsCalls)).toEqual([])
})

import { test, expect } from '@playwright/test'

const game = {
  id: 'ruleset-context-game',
  slug: 'ruleset-context-game',
  title: 'RuleSet Context Game',
  title_ja: 'ルールセット境界確認ゲーム',
  summary: '現在の版と出典境界を確認します。',
  identity_status: 'verified',
  source_trust: 'official_publisher',
  content_review_status: 'review_required',
  rules_content: '## ルール\n- 確認済みです。',
  setup_summary: null,
  gameplay_summary: null,
  end_game_summary: null,
}

test('現在のactive RuleSetを版・platform・language付きで表示する', async ({ page }) => {
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === `/api/games/${game.slug}`) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === `/api/games/${game.slug}/rule-sets`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          schema_version: '1.0',
          status: 'available',
          game_id: game.id,
          slug: game.slug,
          rulesets: [
            {
              ruleset_id: 'current-base',
              game_id: game.id,
              version: 1,
              schema_version: '1.0',
              language_code: 'en',
              edition_label: "Grandpa Beck's Games current edition",
              revision_label: 'current-web-rulebook-1764178570',
              platform: 'physical',
              status: 'active',
              verification_status: 'source_bound',
              is_active: true,
              source_ids: ['publisher-rulebook'],
            },
            {
              ruleset_id: 'old-edition',
              game_id: game.id,
              version: 1,
              schema_version: '1.0',
              language_code: 'en',
              edition_label: 'Earlier edition',
              platform: 'physical',
              status: 'superseded',
              verification_status: 'source_bound',
              is_active: false,
              source_ids: ['old-rulebook'],
            },
          ],
        }),
      })
      return
    }
    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'not found' }) })
  })

  await page.goto(`/games/${game.slug}`)

  const context = page.getByLabel('現在のルールセット')
  await expect(context).toBeVisible()
  await expect(context.getByText('出典に結び付いたルールセット', { exact: true })).toBeVisible()
  await expect(context.getByText("版: Grandpa Beck's Games current edition / プラットフォーム: physical / 言語: en / 改訂: current-web-rulebook-1764178570", { exact: true })).toBeVisible()
  await expect(context.getByText('Earlier edition')).toHaveCount(0)
  await expect(page.getByText('REVIEW REQUIRED', { exact: true })).toBeVisible()
})

test('active RuleSetが複数なら勝手に1件へ絞らず両方表示する', async ({ page }) => {
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === `/api/games/${game.slug}`) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === `/api/games/${game.slug}/rule-sets`) {
      const base = {
        game_id: game.id,
        version: 1,
        schema_version: '1.0',
        language_code: 'en',
        edition_label: 'Current edition',
        platform: 'physical',
        status: 'active',
        verification_status: 'source_bound',
        is_active: true,
        source_ids: [],
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          schema_version: '1.0', status: 'available', game_id: game.id, slug: game.slug,
          rulesets: [
            { ...base, ruleset_id: 'base' },
            { ...base, ruleset_id: 'variant', variant_label: '2-player', base_rule_set_id: 'base', relation_type: 'variant_of' },
          ],
        }),
      })
      return
    }
    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'not found' }) })
  })

  await page.goto(`/games/${game.slug}`)
  const context = page.getByLabel('現在のルールセット')
  await expect(context.locator('li')).toHaveCount(2)
  await expect(context.getByText(/バリアント: 2-player/)).toBeVisible()
})

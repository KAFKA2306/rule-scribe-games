import { test, expect } from '@playwright/test'

const slug = 'evidence-boundary-game'

function gameFixture() {
  return {
    id: slug,
    slug,
    title: 'Evidence Boundary Game',
    title_ja: '根拠表示境界ゲーム',
    summary: '根拠資料の件数と長い資料名を確認するためのテスト専用データです。',
    identity_status: 'verified',
    source_trust: 'official_publisher',
    content_review_status: 'unknown',
    rules_content: '## 詳細ルール\n- 確認済みの裁定です。',
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
  }
}

async function installFixture(page, bindings) {
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url())

    if (url.pathname === `/api/games/${slug}`) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: gameFixture() }) })
      return
    }

    if (url.pathname === `/api/games/${slug}/glossary`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          entries: [{
            concept_id: 'boundary-rule',
            label: '境界ルール',
            aliases: [],
            rule_references: [{
              rule_set_id: 'ruleset-1',
              rule_id: 'rule-1',
              verification_status: 'source_bound',
            }],
          }],
        }),
      })
      return
    }

    if (url.pathname === `/api/games/${slug}/presentation`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          rule_set_id: 'ruleset-1',
          setup: { status: 'available', items: [{ rule_id: 'rule-1', text: '確認済みの裁定' }] },
          game_flow: { status: 'not_available', items: [] },
          end_condition: { status: 'not_available', items: [] },
          scoring: { status: 'not_available', items: [] },
        }),
      })
      return
    }

    if (url.pathname === `/api/games/${slug}/evidence`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          claims: [{
            support_status: 'supported',
            claim: { lifecycle_status: 'accepted' },
            bindings,
          }],
        }),
      })
      return
    }

    if (url.pathname === '/api/concepts/boundary-rule') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ concept_id: 'boundary-rule', label: '境界ルール' }),
      })
      return
    }

    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'not found' }) })
  })
}

function sourceBinding(id, publisherName) {
  return {
    binding: { binding_id: id, relation: 'supports' },
    source: {
      source_id: `source-${id}`,
      publisher_name: publisherName,
      source_type: 'official_faq',
      url: `https://example.com/${id}`,
      revision_label: 'current',
      language_code: 'en',
      platform: 'physical',
    },
    locator: { section_heading: `FAQ / ${id}` },
  }
}

async function openEvidence(page) {
  await page.goto(`/games/${slug}`)
  await page.getByRole('button', { name: '境界ルール', exact: true }).click()
  await expect(page.getByText('確認済みの裁定', { exact: true })).toBeVisible()
  await page.getByText('根拠を確認', { exact: true }).click()
}

test('根拠0件では空の一覧を作らず未登録を明示する', async ({ page }) => {
  await installFixture(page, [])
  await openEvidence(page)

  await expect(page.getByText('このルールの根拠は登録されていません。', { exact: true })).toBeVisible()
  await expect(page.getByRole('list', { name: 'このルールの根拠' })).toHaveCount(0)
})

test('根拠1件では1件だけ表示し重複しない', async ({ page }) => {
  await installFixture(page, [sourceBinding('one', 'Example Games')])
  await openEvidence(page)

  const evidenceList = page.getByRole('list', { name: 'このルールの根拠' })
  await expect(evidenceList).toBeVisible()
  await expect(evidenceList.getByRole('listitem')).toHaveCount(1)
  await expect(page.getByRole('link', { name: 'Example Games（公式FAQ）', exact: true })).toHaveCount(1)
})

test('根拠が複数でも各資料を独立表示し長い日本語・英語名で横にはみ出さない', async ({ page }) => {
  const longJapaneseTitle = '非常に長い出版社資料名でも利用者が根拠を識別できることを確認するための公式サポート資料'
  const longEnglishTitle = 'Grandpa Beck Games International Rules Support and Frequently Asked Questions Documentation Archive'
  await installFixture(page, [
    sourceBinding('jp-long', longJapaneseTitle),
    sourceBinding('en-long', longEnglishTitle),
    sourceBinding('third', 'Another Publisher'),
  ])
  await openEvidence(page)

  const evidenceList = page.getByRole('list', { name: 'このルールの根拠' })
  await expect(evidenceList.getByRole('listitem')).toHaveCount(3)
  await expect(page.getByRole('link', { name: `${longJapaneseTitle}（公式FAQ）`, exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: `${longEnglishTitle}（公式FAQ）`, exact: true })).toBeVisible()

  const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(horizontalOverflow).toBe(false)
})

import { test, expect } from '@playwright/test'

async function mockGame(page, game) {
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
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games: [] }),
    })
  })
}

test('canonical rulesがないゲームはclient側でも基本情報と表示する', async ({ page }) => {
  const game = {
    id: 'game-without-rules',
    slug: 'game-without-rules',
    title: 'Game Without Rules',
    title_ja: 'ルール未確認ゲーム',
    summary: '基本情報だけを確認できるゲームです。',
    identity_status: 'verified',
    source_trust: 'official_publisher',
    content_review_status: 'review_required',
    rules_content: null,
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
  }

  await mockGame(page, game)
  await page.goto(`/games/${game.slug}`)

  await expect(page).toHaveTitle('「ルール未確認ゲーム」の基本情報 | ボドゲのミカタ')
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toHaveCount(0)
  await expect(page.getByText(game.summary, { exact: true })).toBeVisible()
  await expect(page.getByText('REVIEW REQUIRED', { exact: true })).toBeVisible()

  await page.goto(`/games/${game.slug}#rules`)
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toHaveCount(0)
  await expect(page.getByText(game.summary, { exact: true })).toBeVisible()
})

test('canonical rulesがあるゲームだけclient側でルール要約と表示する', async ({ page }) => {
  const game = {
    id: 'game-with-rules',
    slug: 'game-with-rules',
    title: 'Game With Rules',
    title_ja: 'ルール確認済みゲーム',
    summary: '出典付きルールを確認できるゲームです。',
    identity_status: 'verified',
    source_trust: 'official_publisher',
    content_review_status: 'unknown',
    rules_content: '## セットアップ\n- 準備します。',
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
  }

  await mockGame(page, game)
  await page.goto(`/games/${game.slug}`)

  await expect(page).toHaveTitle('「ルール確認済みゲーム」のルール・インスト要約 | ボドゲのミカタ')
  await expect(page.getByRole('button', { name: '詳しいルール', exact: true })).toBeVisible()
})

test('部分的な要点だけを表示し、keyboardで同じゲームの詳細ルールへ進める', async ({ page }) => {
  const game = {
    id: 'game-with-partial-summary',
    slug: 'game-with-partial-summary',
    title: 'Game With Partial Summary',
    title_ja: '部分要点ゲーム',
    summary: '確認できた要点と詳細ルールを同じゲーム情報から表示します。',
    identity_status: 'verified',
    source_trust: 'official_publisher',
    content_review_status: 'review_required',
    source_url: 'https://example.com/official-rules',
    rules_content: '## 詳細ルール\n- 確認済みの手順です。',
    setup_summary: '確認済みの準備だけを表示します。',
    gameplay_summary: null,
    end_game_summary: null,
  }

  await mockGame(page, game)
  await page.goto(`/games/${game.slug}`)

  await expect(page.getByRole('button', { name: '準備・流れ・終了', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByText(game.setup_summary, { exact: true })).toBeVisible()
  await expect(page.getByText('未確認です', { exact: true })).toHaveCount(0)
  await expect(page.getByText('REVIEW REQUIRED', { exact: true })).toBeVisible()

  const rulesButton = page.getByRole('button', { name: '詳しいルール', exact: true })
  await rulesButton.focus()
  await expect(rulesButton).toBeFocused()
  await page.keyboard.press('Enter')

  await expect(page).toHaveURL(/#rules$/)
  await expect(rulesButton).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('heading', { name: '詳細ルール', exact: true })).toBeVisible()
  await expect(page.getByText('REVIEW REQUIRED', { exact: true })).toBeVisible()
})

test('根拠資料の正式な種類を利用者向けの日本語で区別する', async ({ page }) => {
  const slug = 'evidence-source-role-game'
  const game = {
    id: slug,
    slug,
    title: 'Evidence Source Role Game',
    title_ja: '根拠資料表示ゲーム',
    summary: '同じルールに結び付いた根拠資料の役割を確認します。',
    identity_status: 'verified',
    source_trust: 'official_publisher',
    content_review_status: 'unknown',
    rules_content: '## 詳細ルール\n- Mermaid裁定を確認します。',
    setup_summary: null,
    gameplay_summary: null,
    end_game_summary: null,
  }

  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url())

    if (url.pathname === `/api/games/${slug}`) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }

    if (url.pathname === `/api/games/${slug}/glossary`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          entries: [{
            concept_id: 'mermaid',
            label: 'Mermaid',
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
          setup: { status: 'available', items: [{ rule_id: 'rule-1', text: 'Mermaid裁定' }] },
          game_flow: { status: 'not_available', items: [] },
          end_condition: { status: 'not_available', items: [] },
          scoring: { status: 'not_available', items: [] },
        }),
      })
      return
    }

    if (url.pathname === `/api/games/${slug}/evidence`) {
      const source = (bindingId, sourceType, sectionHeading) => ({
        binding: { binding_id: bindingId, relation: 'supports' },
        source: {
          source_id: `source-${bindingId}`,
          publisher_name: "Grandpa Beck's Games",
          source_type: sourceType,
          url: 'https://www.grandpabecksgames.com/pages/skull-king',
          revision_label: 'current',
          language_code: 'en',
          platform: 'physical',
        },
        locator: { section_heading: sectionHeading },
      })
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          claims: [{
            support_status: 'supported',
            claim: { lifecycle_status: 'accepted' },
            bindings: [
              source('rulebook', 'rulebook', 'PLAYING'),
              source('faq', 'official_faq', 'FAQ / Mermaid'),
              source('errata', 'official_errata', 'Errata'),
              source('clarification', 'official_clarification', 'Clarification'),
              source('unknown', 'publisher_blog', 'Blog'),
            ],
          }],
        }),
      })
      return
    }

    if (url.pathname === '/api/concepts/mermaid') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ concept_id: 'mermaid', label: 'Mermaid' }),
      })
      return
    }

    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'not found' }) })
  })

  await page.goto(`/games/${slug}`)
  await page.getByRole('button', { name: 'Mermaid', exact: true }).click()
  await expect(page.getByText('Mermaid裁定', { exact: true })).toBeVisible()
  await page.getByText('根拠を確認', { exact: true }).click()

  await expect(page.getByText('資料: ルールブック')).toBeVisible()
  await expect(page.getByText('資料: 公式FAQ')).toBeVisible()
  await expect(page.getByText('資料: 公式エラッタ')).toBeVisible()
  await expect(page.getByText('資料: 公式補足')).toBeVisible()
  await expect(page.getByText('資料: publisher_blog')).toBeVisible()
  await expect(page.getByText('資料: official_faq')).toHaveCount(0)

  const officialSourceUrl = 'https://www.grandpabecksgames.com/pages/skull-king'
  const rulebookLink = page.getByRole('link', { name: "Grandpa Beck's Games（ルールブック）", exact: true })
  const faqLink = page.getByRole('link', { name: "Grandpa Beck's Games（公式FAQ）", exact: true })
  const errataLink = page.getByRole('link', { name: "Grandpa Beck's Games（公式エラッタ）", exact: true })
  const clarificationLink = page.getByRole('link', { name: "Grandpa Beck's Games（公式補足）", exact: true })
  const unknownLink = page.getByRole('link', { name: "Grandpa Beck's Games（publisher_blog）", exact: true })

  await expect(rulebookLink).toHaveAttribute('href', officialSourceUrl)
  await expect(faqLink).toHaveAttribute('href', officialSourceUrl)
  await expect(errataLink).toHaveAttribute('href', officialSourceUrl)
  await expect(clarificationLink).toHaveAttribute('href', officialSourceUrl)
  await expect(unknownLink).toHaveAttribute('href', officialSourceUrl)

  await faqLink.focus()
  await expect(faqLink).toBeFocused()
})
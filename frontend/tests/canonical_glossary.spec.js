import { test, expect } from '@playwright/test'

const game = {
  id: 901,
  slug: 'glossary-test',
  title: 'Glossary Test',
  title_ja: '用語集テスト',
  min_players: 2,
  max_players: 4,
  play_time: 30,
  min_age: 10,
  published_year: 2026,
  summary: '用語集表示の回帰テスト用ゲーム。',
  source_url: 'https://example.com/source',
  source_trust: 'official_publisher',
  content_review_status: 'review_required',
  rules_content: '# Rules\n\n## 得点\n\n得点を計算します。',
  structured_data: {
    keywords: [{ term: '旧データの用語', description: '正準用語集ではない旧データ' }],
    pro_tips: ['旧データの未確認ヒント'],
    rule_mistakes: ['旧データの未確認ルール誤り'],
    strategy_analysis: '旧データの未確認戦略',
    persona_reviews: [{ persona: '旧AIレビュー', rating: 10, review_text: '旧データの未確認評価' }],
  },
}

async function mockGameAndGlossary(page, glossaryResponse) {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/glossary-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === '/api/games/glossary-test/glossary') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(glossaryResponse) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
}

test('正準用語集が未整備なら旧structured_dataを公開表示へ戻さない', async ({ page }) => {
  await mockGameAndGlossary(page, { status: 'not_available', entries: [] })
  await page.goto('/games/glossary-test#rules')

  const glossary = page.locator('[aria-label="用語集"]')
  await expect(glossary.getByText('用語集の正準データは未整備です。', { exact: true })).toBeVisible()
  await expect(page.getByText('旧データの用語')).toHaveCount(0)
  await expect(page.getByText('旧データの未確認ヒント')).toHaveCount(0)
  await expect(page.getByText('旧データの未確認ルール誤り')).toHaveCount(0)
  await expect(page.getByText('旧データの未確認戦略')).toHaveCount(0)
  await expect(page.getByText('旧AIレビュー')).toHaveCount(0)
  await expect(page.getByText('旧データの未確認評価')).toHaveCount(0)
  await expect(page.getByRole('button', { name: '戦略', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'レビュー', exact: true })).toHaveCount(0)
  await expect(page).toHaveTitle(/「用語集テスト」のルール・インスト要約/)
})

test('正準用語集の取得失敗を旧keywordsで隠さず明示する', async ({ page }) => {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/glossary-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === '/api/games/glossary-test/glossary') {
      await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'unavailable' }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/glossary-test#rules')
  const glossary = page.locator('[aria-label="用語集"]')
  await expect(glossary.getByRole('alert')).toHaveText('用語集の正準データを取得できませんでした。')
  await expect(page.getByText('旧データの用語')).toHaveCount(0)
})

test('旧keywordsがなくても正準用語集がavailableなら表示する', async ({ page }) => {
  const gameWithoutLegacyKeywords = {
    ...game,
    structured_data: { keywords: [] },
  }

  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/glossary-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: gameWithoutLegacyKeywords }) })
      return
    }
    if (url.pathname === '/api/games/glossary-test/glossary') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          entries: [{ concept_id: 'scoring', label: '得点', definition: 'ゲームの得点に関する用語です。', aliases: [] }],
        }),
      })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/glossary-test#rules')
  const glossary = page.locator('[aria-label="用語集"]')
  await expect(glossary.getByRole('button', { name: '得点', exact: true })).toBeVisible()
})

test('正準用語集を日本語名と英語別名のどちらからでも検索できる', async ({ page }) => {
  await mockGameAndGlossary(page, {
    status: 'available',
    entries: [
      {
        concept_id: 'zero-bid',
        label: '0ビッド',
        definition: '0を宣言したビッドです。',
        aliases: ['0 bid', 'zero bid'],
      },
      {
        concept_id: 'mermaid',
        label: 'Mermaid',
        definition: '特殊カードです。',
        aliases: ['人魚'],
      },
    ],
  })
  await page.goto('/games/glossary-test#rules')

  const glossary = page.locator('[aria-label="用語集"]')
  const search = glossary.getByRole('searchbox', { name: '用語集を検索' })

  await search.fill('0 bid')
  await expect(glossary.getByRole('status')).toHaveText('1件の用語が見つかりました')
  await expect(glossary.getByRole('button', { name: '0ビッド', exact: true })).toBeVisible()
  await expect(glossary.getByRole('button', { name: 'Mermaid', exact: true })).toHaveCount(0)

  await search.fill('人魚')
  await expect(glossary.getByRole('status')).toHaveText('1件の用語が見つかりました')
  await expect(glossary.getByRole('button', { name: 'Mermaid', exact: true })).toBeVisible()
})

test('未確認の関連ルールは表示せず、確認済みの参照と登録済み出典だけ表示する', async ({ page }) => {
  await mockGameAndGlossary(page, {
    status: 'available',
    entries: [
      {
        concept_id: 'scoring',
        label: '得点',
        definition: 'ゲームの得点に関する用語です。',
        aliases: [],
        rule_references: [
          {
            rule_id: 'rule-unverified',
            node_type: 'scoring',
            normalized_statement: '未確認の得点ルールです。',
            reference_kind: 'mentions',
            verification_status: 'unknown',
            source_url: 'https://example.com/unverified-source',
          },
          {
            rule_id: 'rule-verified',
            node_type: 'scoring',
            normalized_statement: '確認済みの得点ルールです。',
            reference_kind: 'defines',
            verification_status: 'verified',
            rule_set_id: 'ruleset-current',
            source_url: 'https://example.com/official-rulebook',
            source_locator: 'rules:scoring',
          },
        ],
      },
    ],
  })
  await page.goto('/games/glossary-test#rules')

  const glossary = page.locator('[aria-label="用語集"]')
  await glossary.getByRole('button', { name: '得点', exact: true }).click()

  await expect(glossary.getByText('確認済みの得点ルールです。', { exact: true })).toBeVisible()
  await expect(glossary.getByText('未確認の得点ルールです。', { exact: true })).toHaveCount(0)
  await expect(glossary.getByRole('link', { name: '出典を確認', exact: true })).toHaveAttribute('href', 'https://example.com/official-rulebook')
  await expect(glossary.locator('a[href="https://example.com/unverified-source"]')).toHaveCount(0)
})

test('関連ルールが未確認だけなら未確認文を隠して状態を明示する', async ({ page }) => {
  await mockGameAndGlossary(page, {
    status: 'available',
    entries: [
      {
        concept_id: 'scoring',
        label: '得点',
        definition: 'ゲームの得点に関する用語です。',
        aliases: [],
        rule_references: [
          {
            rule_id: 'rule-unverified',
            node_type: 'scoring',
            normalized_statement: '未確認の得点ルールです。',
            reference_kind: 'mentions',
            verification_status: 'unknown',
          },
        ],
      },
    ],
  })
  await page.goto('/games/glossary-test#rules')

  const glossary = page.locator('[aria-label="用語集"]')
  await glossary.getByRole('button', { name: '得点', exact: true }).click()

  await expect(glossary.getByText('未確認の得点ルールです。', { exact: true })).toHaveCount(0)
  await expect(glossary.getByText('確認済みの関連ルールはありません。', { exact: true })).toBeVisible()
})

test('確認済みRuleNodeを同じRuleSetの正準Presentation ProjectionからRuleNode単位で直接確認できる', async ({ page }) => {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/glossary-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === '/api/games/glossary-test/glossary') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          entries: [{
            concept_id: 'scoring',
            label: '得点',
            definition: 'ゲームの得点に関する用語です。',
            aliases: [],
            rule_references: [{
              rule_id: 'rule-verified',
              node_type: 'scoring',
              normalized_statement: '確認済みの得点ルールです。',
              reference_kind: 'defines',
              verification_status: 'source_bound',
              rule_set_id: 'ruleset-current',
              source_url: 'https://example.com/official-rulebook',
            }],
          }],
        }),
      })
      return
    }
    if (url.pathname === '/api/games/glossary-test/presentation') {
      expect(url.searchParams.get('rule_set_id')).toBe('ruleset-current')
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          rule_set_id: 'ruleset-current',
          setup: { status: 'not_available', items: [] },
          game_flow: { status: 'not_available', items: [] },
          end_condition: { status: 'not_available', items: [] },
          scoring: { status: 'available', items: [{ rule_id: 'rule-verified', text: '確認済みの得点ルールです。' }] },
        }),
      })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })
  await page.route('**/api/concepts/**', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ concept: {}, game_backlinks: [] }),
  }))

  await page.goto('/games/glossary-test#rules')
  const glossary = page.locator('[aria-label="用語集"]')
  await glossary.getByRole('button', { name: '得点', exact: true }).click()

  const localLink = glossary.getByRole('link', { name: '詳しいルールで確認', exact: true })
  await expect(localLink).toHaveAttribute('href', '#rule-node-rule-verified')
  await localLink.click()

  await expect(page).toHaveURL(/#rule-node-rule-verified$/)
  const ruleNode = page.locator('#rule-node-rule-verified')
  await expect(ruleNode).toContainText('確認済みの得点ルールです。')
  await expect(ruleNode).toBeFocused()

  await page.reload()
  await expect(page).toHaveURL(/#rule-node-rule-verified$/)
  await expect(ruleNode).toContainText('確認済みの得点ルールです。')
  await expect(ruleNode).toBeFocused()
})
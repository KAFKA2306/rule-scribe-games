import { test, expect } from '@playwright/test'

const game = {
  id: 902,
  slug: 'glossary-player-count-test',
  title: 'Glossary Player Count Test',
  title_ja: '用語集人数条件テスト',
  min_players: 2,
  max_players: 8,
  play_time: 30,
  min_age: 8,
  published_year: 2026,
  summary: '用語集の人数条件表示を確認するテスト用ゲーム。',
  source_url: 'https://example.com/source',
  source_trust: 'official_publisher',
  content_review_status: 'review_required',
  rules_content: '# Rules\n\n## 特殊カード\n\n特殊カードのルールです。',
  structured_data: {},
}

test('確認済みRuleReferenceの人数条件を明示し、条件なしを一般人数として推測しない', async ({ page }) => {
  await page.route('**/api/games**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/glossary-player-count-test') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game }) })
      return
    }
    if (url.pathname === '/api/games/glossary-player-count-test/glossary') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'available',
          entries: [{
            concept_id: 'component.special-card',
            label: '特殊カード',
            definition: '特殊な効果を持つカードです。',
            aliases: [],
            rule_references: [
              {
                rule_id: 'two-player.tigress',
                node_type: 'exception',
                normalized_statement: 'GraybeardがTigressを出した場合はEscapeとして扱う。',
                reference_kind: 'mentions',
                verification_status: 'source_bound',
                rule_set_id: 'ruleset-current',
                player_count: 2,
                source_url: 'https://example.com/official-faq',
              },
              {
                rule_id: 'turn.follow-suit',
                node_type: 'condition',
                normalized_statement: '特殊カードはリードスートに関係なく出せる。',
                reference_kind: 'mentions',
                verification_status: 'source_bound',
                rule_set_id: 'ruleset-current',
                player_count: null,
                source_url: 'https://example.com/official-rulebook',
              },
            ],
          }],
        }),
      })
      return
    }
    if (url.pathname.startsWith('/api/concepts/')) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game_backlinks: [] }) })
      return
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [] }) })
  })

  await page.goto('/games/glossary-player-count-test#rules')
  const glossary = page.locator('[aria-label="用語集"]')
  await glossary.getByRole('button', { name: '特殊カード', exact: true }).click()

  await expect(glossary.getByText('2人用', { exact: true })).toBeVisible()
  await expect(glossary.getByText('GraybeardがTigressを出した場合はEscapeとして扱う。', { exact: true })).toBeVisible()
  await expect(glossary.getByText('特殊カードはリードスートに関係なく出せる。', { exact: true })).toBeVisible()
  await expect(glossary.getByText('4人用', { exact: true })).toHaveCount(0)
})

import { test, expect } from '@playwright/test'
import {
  getCuratedRuleGuide,
  listCuratedRuleGuides,
  validateRuleGuide,
} from '../src/lib/curatedRuleGuides.js'

const ipso = {
  id: 'ipso-0000-4000-8000-000000000001',
  slug: 'ipso',
  title: 'IPSO',
  title_ja: 'イプソ (IPSO)',
  min_players: 2,
  max_players: 6,
  play_time: 15,
  min_age: 7,
  published_year: 2025,
  summary: '数字カードを昇順に並べ、色と星を活かして得点するカードゲーム。',
  description: 'IPSO description',
  setup_summary: '14枚で5・4・3・2枚の4段ピラミッドを作り、頂点に星カードを置く。',
  gameplay_summary: '中央2枚から1枚を選び、裏向きカード1枚と交換する。',
  end_game_summary: '全員が14枚を表向きにした後、星カードの最終処理を行い、全員終了で得点計算する。',
  official_url: 'https://en.gigamic.com/index.php?controller=attachment&id_attachment=668',
  rules_content: '# IPSO\n\n## 手番\n中央2枚から1枚選び、裏向きカードと交換します。\n\n## 終了\n全員の最終処理後に終了します。',
  structured_data: {},
  infographics: {
    turn_flow: '/assets/legacy-unverified-ipso.svg',
  },
  infographics_reviewed: false,
}

async function mockIpsoApi(page) {
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/games/ipso') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ game: ipso }) })
      return
    }
    if (url.pathname === '/api/games') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [ipso], total: 1 }) })
      return
    }
    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'not found' }) })
  })
}

test('all production curated guides satisfy evidence and semantic contracts', () => {
  for (const { slug, guide } of listCuratedRuleGuides()) {
    const result = validateRuleGuide(guide)
    expect(result.errors, `${slug}: ${result.errors.join(', ')}`).toEqual([])
    expect(getCuratedRuleGuide(slug)).not.toBeNull()
  }
})

test('accuracy gate rejects action-count and stale-version mismatches', () => {
  const splendor = getCuratedRuleGuide('splendor')
  expect(splendor).not.toBeNull()

  const wrongActionCount = {
    ...splendor,
    quick: {
      ...splendor.quick,
      actions: splendor.quick.actions.slice(0, 3),
    },
  }
  expect(validateRuleGuide(wrongActionCount).errors).toContain('action count mismatch: expected 4')

  const stale = {
    ...splendor,
    ruleVersion: 'stale-version',
  }
  expect(validateRuleGuide(stale).errors).toContain('guide/source ruleVersion mismatch')
})

test('unreviewed guide fails closed instead of producing quick rules', () => {
  const result = validateRuleGuide({
    reviewed: false,
    ruleVersion: 'x',
    source: { url: 'https://example.com/rules', ruleVersion: 'x' },
    quick: { turnSteps: ['step'], end: 'end' },
    flow: [{ id: 'a' }, { id: 'b' }],
  })
  expect(result.valid).toBe(false)
  expect(result.errors).toContain('guide is not reviewed')
})

test('new user can search IPSO and reach quick rules, scoring, diagram and source', async ({ page }, testInfo) => {
  await mockIpsoApi(page)

  await page.goto('/')
  await expect(page.getByText('イプソ (IPSO)', { exact: true }).first()).toBeVisible()
  await page.getByLabel('ゲームを検索').fill('IPSO')
  await expect(page.getByText('1 RESULTS')).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath(`new-user-home-${testInfo.project.name}.png`), animations: 'disabled' })

  await page.getByRole('link', { name: /イプソ \(IPSO\)/ }).first().click()
  await expect(page).toHaveURL(/\/games\/ipso$/)

  const quick = page.getByTestId('quick-rules-panel')
  await expect(quick).toBeVisible()
  await expect(quick.getByText('今の手番ですること')).toBeVisible()
  await expect(quick.getByText('中央の表向き2枚から1枚を選ぶ。')).toBeVisible()
  await expect(quick.getByText(/全員の14枚が表向き/)).toBeVisible()
  await expect(quick.getByText('公式ルール確認済み')).toBeVisible()
  await quick.scrollIntoViewIfNeeded()
  await page.screenshot({ path: testInfo.outputPath(`ipso-quick-rules-${testInfo.project.name}.png`), animations: 'disabled' })

  const scoring = page.getByTestId('scoring-breakdown')
  await scoring.locator('summary').first().click()
  await expect(scoring.getByText(/昇順でない段は0点/)).toBeVisible()
  await expect(scoring.getByText('合計 26点')).toBeVisible()
  await scoring.scrollIntoViewIfNeeded()
  await page.screenshot({ path: testInfo.outputPath(`ipso-scoring-${testInfo.project.name}.png`), animations: 'disabled' })

  await page.getByRole('button', { name: '図で見る', exact: true }).first().click()
  const flow = page.getByTestId('rule-flow-diagram')
  await expect(flow).toBeVisible()
  await expect(flow.getByText('全員の14枚がすべて表向き？')).toBeVisible()
  await expect(flow.getByText('星カードをどうする？')).toBeVisible()
  await expect(flow.getByRole('link', { name: 'Gigamic 公式ルール' })).toHaveAttribute('href', ipso.official_url)
  await expect(page.locator('.infographics-gallery')).toHaveCount(0)
  await flow.scrollIntoViewIfNeeded()
  await page.screenshot({ path: testInfo.outputPath(`ipso-turn-flow-${testInfo.project.name}.png`), animations: 'disabled' })

  const geometry = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    quickWidth: document.querySelector('[data-testid="quick-rules-panel"]')?.getBoundingClientRect().width || 0,
  }))
  expect(geometry.scrollWidth).toBeLessThanOrEqual(geometry.clientWidth + 1)
  expect(geometry.quickWidth).toBeLessThanOrEqual(geometry.clientWidth)
})
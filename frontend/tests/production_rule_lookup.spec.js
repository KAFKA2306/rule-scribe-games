import { test, expect } from '@playwright/test'

const productionBaseURL = process.env.PLAYWRIGHT_BASE_URL

test.skip(!productionBaseURL, 'production URLが指定されたdeploy後検証でのみ実行する')

async function expectNoPageOverflow(page) {
  const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
  expect(hasOverflow).toBe(false)
}

async function openCanonicalRuleFromSearch(page, query, ruleId, expectedSource, expectedPlayerCount = null) {
  const search = page.getByRole('searchbox', { name: '裁定・用語を入力' })
  const results = page.getByRole('list', { name: '用語集の検索結果' })

  await search.fill(query)
  await expect(results).toBeVisible()
  await expect(results.getByText(`出典: ${expectedSource}`, { exact: true }).first()).toBeVisible()
  if (expectedPlayerCount !== null) {
    await expect(results.getByText(`人数条件: ${expectedPlayerCount}人`, { exact: true }).first()).toBeVisible()
  }

  await results.getByRole('link').first().click()

  const glossary = page.locator('[aria-label="用語集"]')
  const sourceLink = glossary.getByRole('link', { name: '出典を確認', exact: true }).first()
  await expect(sourceLink).toBeVisible()
  await expect(sourceLink).toHaveAttribute('href', /^https:\/\/www\.grandpabecksgames\.com\//)

  const ruleLink = glossary.locator(`a[href="#rule-node-${ruleId}"]`).first()
  await expect(ruleLink).toBeVisible()
  await ruleLink.click()

  const escapedRuleId = ruleId.replaceAll('.', '\\.')
  const target = page.locator(`#rule-node-${escapedRuleId}`)
  await expect(target).toBeVisible()
  await expect(page).toHaveURL(new RegExp(`#rule-node-${escapedRuleId}$`))
  await expectNoPageOverflow(page)
}

test('productionのSkull Kingで代表queryから確認済みRuleNodeと公式出典へ到達できる', async ({ page }) => {
  await page.goto('/games/skull-king#rules', { waitUntil: 'networkidle' })
  await expect(page.getByRole('searchbox', { name: '裁定・用語を入力' })).toBeVisible()
  await expectNoPageOverflow(page)

  await openCanonicalRuleFromSearch(page, '0 bid', 'scoring.zero-bid', 'ルールブック')
  await openCanonicalRuleFromSearch(page, 'FAQ Mermaid', 'resolution.mermaid-triad', 'FAQ')
  await openCanonicalRuleFromSearch(page, 'FAQ 2人', 'two-player.tigress', 'FAQ', 2)
})

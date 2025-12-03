import { test, expect } from '@playwright/test'

test('has title and loads games', async ({ page }) => {
  await page.goto('/')

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/ボドゲのミカタ/)

  // Check for the main heading
  await expect(page.getByRole('heading', { name: 'RuleScribe Games' })).toBeVisible()

  // Check if at least one game card is present (Catan from seed)
  await expect(page.getByText('Catan')).toBeVisible()
})

test('can navigate to game details', async ({ page }) => {
  await page.goto('/')

  // Click on Catan
  await page.getByText('Catan').click()

  // Check URL
  await expect(page).toHaveURL(/.*\/game\/.*/)

  // Check for Rules section
  await expect(page.getByRole('heading', { name: 'Rules' })).toBeVisible()

  // Check for specific rule content
  await expect(page.getByText('Collect resources and build settlements')).toBeVisible()
})

test('can search for games', async ({ page }) => {
  await page.goto('/')

  // Search for Catan
  await page.getByPlaceholder('Search games...').fill('Catan')
  await expect(page.getByText('Catan')).toBeVisible()

  // Search for non-existent game
  await page.getByPlaceholder('Search games...').fill('NonExistentGame')
  await expect(page.getByText('No games found')).toBeVisible()
})

test('displays valid LLM-generated content (Poker)', async ({ page }) => {
  await page.goto('/')
  await page.getByPlaceholder('Search games...').fill('Poker')
  await page.getByText("Texas Hold'em Poker").click()

  // Verify complex nested structure
  await expect(page.getByText('Royal Flush > Straight Flush')).toBeVisible()
})

test('handles malformed LLM content gracefully', async ({ page }) => {
  await page.goto('/')
  await page.getByPlaceholder('Search games...').fill('Broken')

  // The game should be visible in the list (title comes from DB column, not JSON)
  await expect(page.getByText('Broken LLM Game')).toBeVisible()

  // Clicking it should not crash the app
  await page.getByText('Broken LLM Game').click()

  // Should show the fallback message from SupabaseGameRepository
  await expect(page.getByText('Error loading rules')).toBeVisible()
})

test('displays complex Agricola data correctly', async ({ page }) => {
  await page.goto('/')
  await page.getByPlaceholder('Search games...').fill('Agricola')
  await page.getByText('Agricola (アグリコラ)').click()

  // Verify rich content rendering
  await expect(page.getByText('120x カード')).toBeVisible() // Component count
  await expect(page.getByText('14ラウンド終了後')).toBeVisible() // Victory condition
})

test('AI generation button state', async ({ page }) => {
  await page.goto('/')

  const generateBtn = page.getByRole('button', { name: 'Generate with AI' })
  const searchInput = page.getByPlaceholder('Search games...')

  // Initially disabled because search is empty
  await expect(generateBtn).toBeVisible()
  await expect(generateBtn).toBeDisabled()

  // Enabled when text is entered
  await searchInput.fill('Monopoly')
  await expect(generateBtn).toBeEnabled()

  // Loading state (mocking the API call would be needed for full test,
  // but we can check if clicking changes text if we could intercept,
  // for now just verifying it's clickable)
})

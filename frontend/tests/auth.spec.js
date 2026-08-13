import { test, expect } from '@playwright/test'

test('configured Google auth control mounts inside existing layout without becoming a root grid item', async ({ page }) => {
  await page.route('**/api/games?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ games: [], total: 0 }),
    })
  })

  await page.goto('/')

  const authControl = page.locator('header [data-auth-control]')
  await expect(authControl).toBeVisible()
  const loginButton = authControl.getByRole('button', { name: 'Googleでログイン' })
  await expect(loginButton).toBeVisible()
  await expect(loginButton).toBeEnabled()

  const directChildren = await page.locator('#root > *').evaluateAll((nodes) => nodes.map((node) => node.tagName))
  expect(directChildren).toEqual(['HEADER', 'ASIDE', 'MAIN'])
})

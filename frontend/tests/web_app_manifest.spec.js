import { test, expect } from '@playwright/test'

test('homepage links to a JSON Web App Manifest', async ({ page, request }) => {
  await page.goto('/')

  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute('href', '/manifest.webmanifest')

  const response = await request.get('/manifest.webmanifest')
  expect(response.ok()).toBeTruthy()
  expect(response.headers()['content-type']).toContain('application/manifest+json')

  const manifest = await response.json()
  expect(manifest).toMatchObject({
    id: '/',
    name: 'ボドゲのミカタ',
    short_name: 'ボドゲのミカタ',
    lang: 'ja',
    start_url: '/',
    scope: '/',
    display: 'standalone',
  })
})

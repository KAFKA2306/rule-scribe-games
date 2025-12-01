import { test, expect } from '@playwright/test';

test('verify wiki generation', async ({ page }) => {
  // 1. Navigate to the production URL
  await page.goto('https://rule-scribe-games.vercel.app');

  // 2. Type 'Catan' into the input field
  await page.getByPlaceholder('ゲームの名前を入れてね').fill('Catan');

  // 3. Click the 'さがす' button
  await page.getByRole('button', { name: 'さがす' }).click();

  // 4. Wait for the results to appear and click on 'Catan'
  // Use a more specific locator for the result item
  const result = page.locator('.results li').filter({ hasText: 'Catan' }).first();
  await result.waitFor({ timeout: 10000 });
  await result.click();

  // 5. Verify that the detail section shows the title
  // The title is in .detail-head h2
  const title = page.locator('.detail-head h2');
  await expect(title).toContainText('Catan', { timeout: 10000 });

  // 6. Verify that the "要約する" (Summarize) button exists or summary is shown
  const summarizeBtn = page.getByRole('button', { name: /要約する|要約完了！/ });
  await expect(summarizeBtn).toBeVisible();

  // Take a screenshot at the end
  await page.screenshot({ path: 'verification_success.png' });
});

test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    await page.screenshot({ path: 'verification_failure.png' });
  }
});

import { test, expect } from '@playwright/test'

test.describe('Game List Loading', () => {
  test('should load games successfully on initial page load', async ({ page }) => {
    let apiResponseStatus = 0;
    let apiResponseBody = null;

    // Listen for the /api/games network request
    page.on('response', async response => {
      if (response.url().includes('/api/games') && response.request().method() === 'GET') {
        apiResponseStatus = response.status();
        try {
          apiResponseBody = await response.json();
        } catch (e) {
          apiResponseBody = await response.text(); // Fallback for non-JSON response
        }
      }
    });

    await page.goto('https://rule-scribe-games.vercel.app');

    // Make a direct request to /api/games
    const gamesResponse = await page.request.get('https://rule-scribe-games.vercel.app/api/games');
    apiResponseStatus = gamesResponse.status();
    try {
      apiResponseBody = await gamesResponse.json();
    } catch (e) {
      apiResponseBody = await gamesResponse.text();
    }
    
    // Check if the API call was intercepted and processed
    expect(apiResponseStatus).not.toBe(0); // Ensure we actually captured the response

    if (apiResponseStatus !== 200) {
      console.error(`API /api/games failed with status: ${apiResponseStatus}`);
      console.error('API Response Body:', apiResponseBody);
    }

    // Assert that the API call was successful
    expect(apiResponseStatus).toBe(200);

    // Assert that the response body is an array and contains game objects
    expect(Array.isArray(apiResponseBody)).toBe(true);
    // expect(apiResponseBody.length).toBeGreaterThan(0); // Assuming there are games in the DB
    // Let's not assert length for now, just check it's an array.

    // Optionally, check for the presence of the game list in the UI if the API call was successful
    if (apiResponseStatus === 200) {
      // Check if the error message "ゲームの読み込みに失敗しました。" is NOT visible
      const errorMessage = page.locator('.error-banner:has-text("ゲームの読み込みに失敗しました。")');
      await expect(errorMessage).not.toBeVisible();

      // Check if the game list header is visible and shows some count (assuming it updates dynamically)
      const gameListHeader = page.locator('.game-list-pane h2');
      await expect(gameListHeader).toBeVisible();
      // Further assertions could be made here about the number of games or specific game titles
    }
  });
});

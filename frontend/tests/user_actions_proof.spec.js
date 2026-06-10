import { test, expect } from '@playwright/test';

// Proof of Redesign and Multi-Perspective Dashboard
test.describe('User Actions Proof - Zero-Fat Dashboard', () => {
  
  test.beforeEach(async ({ page }) => {
    // Mocking the games API for stable proof
    await page.route('**/api/games?limit=1000&offset=0', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          games: [
            { 
              id: '1', slug: 'ark-nova', title_ja: 'アーク・ノヴァ', 
              summary: '動物園経営の最高峰', min_players: 1, max_players: 4, 
              play_time: 150, strategy_tier: 'S', 
              structured_data: { mechanics: ['Hand Management', 'Enclosure Building'] } 
            },
            { 
              id: '2', slug: 'scythe', title_ja: 'サイズ -大鎌戦役-', 
              summary: '架空の戦後ヨーロッパでの覇権争い', min_players: 1, max_players: 5, 
              play_time: 115, strategy_tier: 'S',
              structured_data: { mechanics: ['Area Control', 'Engine Building'] } 
            }
          ],
          total: 2,
          limit: 1000,
          offset: 0
        }),
      });
    });

    await page.goto('/');
  });

  test('Perspective 1: Dashboard Density and Counts', async ({ page }) => {
    // 1. Verify total count in header
    const dbStatus = page.locator('.db-status');
    await expect(dbStatus).toContainText('2 GAMES');
    console.log('✅ Evidence: Header shows correct total game count.');

    // 2. Verify results count in control panel
    const resultsCount = page.locator('.active-filters span');
    await expect(resultsCount).toContainText('2 RESULTS');
    console.log('✅ Evidence: Results count is visible and accurate.');
  });

  test('Perspective 2: Comparison Battle Flow', async ({ page }) => {
    // 1. Click COMPARE on first game (becomes READY)
    await page.locator('button:has-text("COMPARE")').first().click();
    
    // 2. Click COMPARE on second game (which is now the ONLY one with "COMPARE" text)
    await page.locator('button:has-text("COMPARE")').click();

    // 3. Verify Battle Tray is visible
    const tray = page.locator('.comparison-tray');
    await expect(tray).toBeVisible();
    await expect(tray).toContainText('BATTLE TRAY');
    console.log('✅ Evidence: Comparison Tray active after user selection.');

    // 4. Start Battle
    await page.click('button:has-text("BATTLE START")');
    
    // 5. Verify Battle View
    await expect(page.locator('h1.game-title')).toContainText('COMPARISON BATTLE');
    await expect(page.locator('.battle-grid')).toBeVisible();
    const battleCols = page.locator('.battle-col');
    await expect(battleCols).toHaveCount(2);
    console.log('✅ Evidence: Comparison Battle mode successfully entered and rendered.');
  });

  test('Perspective 3: Inst Coach and Connections', async ({ page }) => {
    // Mocking specific game detail
    await page.route('**/api/games/ark-nova', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '1', slug: 'ark-nova', title_ja: 'アーク・ノヴァ',
          rules_content: '# Rules for Ark Nova',
          strategy_tier: 'S',
          structured_data: { 
            mechanics: ['Hand Management'],
            pro_tips: ['Cycle your cards early'],
            rule_mistakes: ["Don't forget the break trigger"]
          }
        }),
      });
    });

    // 1. Navigate to Ark Nova
    await page.click('.asset-card >> nth=0');
    await expect(page.locator('.game-title').first()).toContainText('アーク・ノヴァ');

    // 2. Verify Inst Coach Tab
    await page.click('button:has-text("INST COACH")');
    await expect(page.locator('.coach-step')).toHaveCount(3);
    await expect(page.locator('.coach-step.active')).toContainText('セットアップ');
    console.log('✅ Evidence: Inst Coach perspective provides step-by-step guidance.');

    // 3. Verify Connections Tab
    await page.click('button:has-text("CONNECTIONS")');
    await expect(page.locator('.pro-card-title').filter({ hasText: 'CONNECTIONS' })).toBeVisible();
    console.log('✅ Evidence: Connections perspective allows exploring mechanical DNA.');
  });
});

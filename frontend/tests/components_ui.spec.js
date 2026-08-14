import { test, expect } from '@playwright/test'

const game = {
  id: '11111111-1111-4111-8111-111111111176',
  slug: 'component-fixture',
  title: 'Component Fixture',
  title_ja: 'コンポーネント・フィクスチャ',
  min_players: 2,
  max_players: 4,
  play_time: 30,
  min_age: 10,
  published_year: 2026,
  summary: 'Schema-driven Components UI fixture.',
  rules_content: '# Fixture Rules\n\nCanonical component UI test fixture.',
  structured_data: {},
}

const componentSets = [
  { component_set_id: 'cards', ruleset_id: 'ruleset-components', canonical_name: 'Cards', kind: 'card' },
  { component_set_id: 'tiles', ruleset_id: 'ruleset-components', canonical_name: 'Tiles', kind: 'tile' },
  { component_set_id: 'tokens', ruleset_id: 'ruleset-components', canonical_name: 'Tokens', kind: 'token' },
  { component_set_id: 'dice', ruleset_id: 'ruleset-components', canonical_name: 'Dice', kind: 'die' },
]

const definitions = [
  { property_key: 'faction', labels: { ja: '派閥' }, value_type: 'enum', cardinality: 'one', enum_values: ['sun', 'moon'], filterable: true, sortable: false },
  { property_key: 'power', labels: { ja: '戦力' }, value_type: 'integer', cardinality: 'one', enum_values: [], unit: 'VP', filterable: true, sortable: true },
  { property_key: 'active', labels: { ja: '有効' }, value_type: 'boolean', cardinality: 'one', enum_values: [], filterable: true, sortable: false },
  { property_key: 'note', labels: { ja: '注記' }, value_type: 'text', cardinality: 'one', enum_values: [], filterable: true, sortable: false },
]

function property(propertyKey, valueType, value) {
  return {
    property_key: propertyKey,
    values: [{ value_type: valueType, value }],
    verification_status: 'unknown',
    source_ids: [],
  }
}

function buildItems() {
  const kinds = [
    ['card', 'cards'],
    ['tile', 'tiles'],
    ['token', 'tokens'],
    ['die', 'dice'],
  ]
  return Array.from({ length: 125 }, (_, index) => {
    const [kind, setId] = kinds[index % kinds.length]
    const name = index === 0 ? 'Scout' : `Component ${String(index + 1).padStart(3, '0')}`
    const componentId = index === 0 ? 'card.scout' : `${kind}.fixture-${index + 1}`
    const faction = index % 2 === 0 ? 'sun' : 'moon'
    const item = {
      component: {
        component_id: componentId,
        ruleset_id: 'ruleset-components',
        component_set_id: setId,
        canonical_name: name,
        kind,
        quantity: index % 7 === 0 ? 2 : null,
        properties: [
          property('faction', 'enum', faction),
          property('power', 'integer', (index % 9) + 1),
          property('active', 'boolean', index % 3 !== 0),
          property('note', 'text', `${kind} fixture ${index + 1}`),
        ],
        abilities: index === 0 ? [{
          ability_id: 'ability.scout',
          printed_text: 'Gain 1 gold.',
          normalized_label: 'Gain gold',
          rule_ids: ['rule.scout'],
          concept_ids: ['resource.gold'],
          verification_status: 'verified',
          source_ids: ['source.publisher'],
        }] : [],
        concept_ids: index === 0 ? ['resource.gold'] : [],
        rule_ids: index === 0 ? ['rule.scout'] : [],
        verification_status: 'unknown',
        source_ids: [],
      },
      property_evidence: {
        faction: {
          status: index === 0 ? 'verified' : 'unknown',
          claim_ids: index === 0 ? ['claim.scout.faction'] : [],
          source_ids: index === 0 ? ['source.publisher'] : [],
        },
        power: { status: 'unknown', claim_ids: [], source_ids: [] },
        active: { status: 'unknown', claim_ids: [], source_ids: [] },
        note: { status: 'unknown', claim_ids: [], source_ids: [] },
      },
      ability_evidence: index === 0 ? {
        'ability.scout': {
          printed_text: { status: 'verified', claim_ids: ['claim.scout.printed'], source_ids: ['source.publisher'] },
          normalized: { status: 'verified', claim_ids: ['claim.scout.normalized'], source_ids: ['source.publisher'] },
        },
      } : {},
    }
    return item
  })
}

async function mockApi(page, { catalogAvailable = true } = {}) {
  const items = buildItems()
  const catalogRequests = []

  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname

    if (path === '/api/games/component-fixture') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(game) })
      return
    }
    if (path === '/api/games/component-fixture/component-catalog-availability') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          schema_version: '1.0',
          status: catalogAvailable ? 'available' : 'not_available',
          game_id: game.id,
          slug: game.slug,
          rule_set_ids: catalogAvailable ? ['ruleset-components'] : [],
        }),
      })
      return
    }
    if (path === '/api/games/component-fixture/component-catalog') {
      catalogRequests.push(url.search)
      const offset = Number(url.searchParams.get('offset') || 0)
      const limit = Number(url.searchParams.get('limit') || 100)
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          schema_version: '1.0',
          status: 'available',
          game_id: game.id,
          slug: game.slug,
          rule_set_id: 'ruleset-components',
          component_sets: componentSets,
          property_definitions: definitions,
          items: items.slice(offset, offset + limit),
          total: items.length,
          limit,
          offset,
        }),
      })
      return
    }
    if (path === '/api/games/component-fixture/glossary') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ schema_version: '1.0', status: 'not_available', game_id: game.id, slug: game.slug, language_code: 'ja', entries: [] }),
      })
      return
    }
    if (path === '/api/games') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ games: [], total: 0 }) })
      return
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'not_available' }) })
  })

  return { catalogRequests }
}

test('catalog absence hides the tab and never requests full components', async ({ page }) => {
  const audit = await mockApi(page, { catalogAvailable: false })
  await page.goto('/games/component-fixture')
  await expect(page.getByRole('heading', { name: game.title_ja })).toBeVisible()
  await expect(page.getByRole('tab', { name: /コンポーネント/ })).toHaveCount(0)
  expect(audit.catalogRequests).toEqual([])
})

test('100+ components load in pages and schema-driven filters work globally', async ({ page }) => {
  const audit = await mockApi(page)
  await page.goto('/games/component-fixture')
  await page.getByRole('tab', { name: /コンポーネント/ }).click()

  await expect(page.getByRole('heading', { name: 'COMPONENTS' })).toBeVisible()
  await expect(page.getByText('125 / 125')).toBeVisible()
  expect(audit.catalogRequests.length).toBe(2)
  expect(audit.catalogRequests.some((query) => query.includes('offset=100'))).toBeTruthy()

  await page.getByLabel('SEARCH').fill('Scout')
  await expect(page.getByText('1 / 125')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Scout' })).toBeVisible()

  await page.getByLabel('SEARCH').fill('')
  await page.getByLabel('派閥').selectOption('sun')
  await expect(page.getByText(/63 \/ 125/)).toBeVisible()

  await page.getByLabel('派閥').selectOption('')
  await page.getByLabel('戦力 最小値').fill('8')
  await expect(page.locator('.component-card')).toHaveCount(27)
})

test('component detail is keyboard reachable and traces field evidence without images', async ({ page }) => {
  await mockApi(page)
  await page.goto('/games/component-fixture')

  const tab = page.getByRole('tab', { name: /コンポーネント/ })
  await tab.focus()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('heading', { name: 'COMPONENTS' })).toBeVisible()

  const firstCard = page.locator('.component-card-button').first()
  await firstCard.focus()
  await page.keyboard.press('Enter')
  const detail = page.getByRole('dialog')
  await expect(detail).toBeVisible()
  await expect(detail.getByRole('heading', { name: 'Scout' })).toBeVisible()
  await expect(detail.getByText('VERIFIED').first()).toBeVisible()
  await expect(detail.getByRole('link', { name: /EVIDENCE/ }).first()).toHaveAttribute('href', /claim\.scout/)
  await expect(detail.getByRole('link', { name: 'resource.gold' })).toHaveAttribute('href', '/api/concepts/resource.gold')
  await expect(detail.locator('img')).toHaveCount(0)
})

test('Components UI has no horizontal page overflow at responsive target widths', async ({ page }) => {
  await mockApi(page)
  await page.goto('/games/component-fixture')
  await page.getByRole('tab', { name: /コンポーネント/ }).click()
  await expect(page.getByText('125 / 125')).toBeVisible()

  const metrics = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    panelWidth: document.querySelector('.components-panel')?.getBoundingClientRect().width || 0,
  }))
  expect(metrics.scrollWidth).toBe(metrics.clientWidth)
  expect(metrics.panelWidth).toBeLessThanOrEqual(metrics.clientWidth)
})

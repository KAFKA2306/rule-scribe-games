import assert from 'node:assert/strict'
import test from 'node:test'

import {
  evidenceLabel,
  filterAndSortComponentItems,
  getPropertyLabel,
  pageOffsets,
  propertyDisplayText,
} from '../src/lib/componentCatalog.js'

const definitions = [
  {
    property_key: 'faction',
    labels: { ja: '派閥', en: 'Faction' },
    value_type: 'enum',
    enum_values: ['sun', 'moon'],
    filterable: true,
  },
  {
    property_key: 'power',
    labels: { ja: '戦力' },
    value_type: 'integer',
    sortable: true,
    unit: 'VP',
  },
  {
    property_key: 'active',
    labels: { ja: '有効' },
    value_type: 'boolean',
    filterable: true,
  },
  {
    property_key: 'note',
    labels: { ja: '注記' },
    value_type: 'text',
    filterable: true,
  },
]

function item(id, name, kind, setId, properties = [], evidence = {}) {
  return {
    component: {
      component_id: id,
      canonical_name: name,
      kind,
      component_set_id: setId,
      quantity: null,
      properties,
      abilities: [],
      concept_ids: [],
      rule_ids: [],
    },
    property_evidence: evidence,
    ability_evidence: {},
  }
}

function prop(propertyKey, valueType, ...values) {
  return {
    property_key: propertyKey,
    values: values.map((value) => ({ value_type: valueType, value })),
  }
}

test('card, tile, token and die use the same generic filter path', () => {
  const items = [
    item('card.scout', 'Scout', 'card', 'cards', [prop('faction', 'enum', 'sun'), prop('power', 'integer', 3)]),
    item('tile.forest', 'Forest', 'tile', 'tiles', [prop('power', 'integer', 1)]),
    item('token.energy', 'Energy', 'token', 'tokens', [prop('active', 'boolean', true)]),
    item('die.action', 'Action Die', 'die', 'dice', [prop('note', 'text', 'attack die')]),
  ]

  assert.deepEqual(
    filterAndSortComponentItems(items, definitions, { search: 'die' }).map((entry) => entry.component.component_id),
    ['die.action'],
  )
  assert.deepEqual(
    filterAndSortComponentItems(items, definitions, { componentSetId: 'tiles' }).map((entry) => entry.component.component_id),
    ['tile.forest'],
  )
})

test('enum, numeric, boolean and text filters are schema driven', () => {
  const items = [
    item('card.sun', 'Sun', 'card', 'cards', [
      prop('faction', 'enum', 'sun'),
      prop('power', 'integer', 4),
      prop('active', 'boolean', true),
      prop('note', 'text', 'fast scout'),
    ]),
    item('card.moon', 'Moon', 'card', 'cards', [
      prop('faction', 'enum', 'moon'),
      prop('power', 'integer', 2),
      prop('active', 'boolean', false),
      prop('note', 'text', 'slow guard'),
    ]),
  ]

  assert.equal(filterAndSortComponentItems(items, definitions, { filters: { faction: 'sun' } }).length, 1)
  assert.equal(filterAndSortComponentItems(items, definitions, { filters: { power: { min: 3, max: '' } } }).length, 1)
  assert.equal(filterAndSortComponentItems(items, definitions, { filters: { active: 'false' } })[0].component.component_id, 'card.moon')
  assert.equal(filterAndSortComponentItems(items, definitions, { filters: { note: 'scout' } })[0].component.component_id, 'card.sun')
})

test('sortable property definitions work without game-specific keys', () => {
  const items = [
    item('card.a', 'A', 'card', 'cards', [prop('power', 'integer', 9)]),
    item('card.b', 'B', 'card', 'cards', [prop('power', 'integer', 2)]),
  ]
  assert.deepEqual(
    filterAndSortComponentItems(items, definitions, { sortKey: 'power', sortDirection: 'asc' })
      .map((entry) => entry.component.component_id),
    ['card.b', 'card.a'],
  )
})

test('unknown future property types fail closed instead of crashing', () => {
  const unknown = { property_key: 'future', labels: { ja: '将来型' }, value_type: 'matrix' }
  const component = item('card.future', 'Future', 'card', 'cards', [prop('future', 'matrix', 'x')])
  assert.equal(propertyDisplayText(component.component, unknown), null)
  assert.equal(filterAndSortComponentItems([component], [unknown], { filters: { future: 'x' } }).length, 1)
})

test('labels, evidence badges and 100+ pagination are deterministic', () => {
  assert.equal(getPropertyLabel(definitions[0], 'ja'), '派閥')
  assert.equal(propertyDisplayText({ properties: [prop('power', 'integer', 3)] }, definitions[1]), '3 VP')
  assert.equal(evidenceLabel({ status: 'verified' }), 'VERIFIED')
  assert.equal(evidenceLabel({ status: 'contested' }), 'CONTESTED')
  assert.equal(evidenceLabel(), 'UNVERIFIED')
  assert.deepEqual(pageOffsets(251, 100), [100, 200])
  assert.deepEqual(pageOffsets(1, 100), [])
})

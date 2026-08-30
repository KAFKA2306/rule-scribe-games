import { test, expect } from '@playwright/test'
import {
  getCuratedRuleGuide,
  listCuratedRuleGuides,
  validateRuleGuide,
} from '../src/lib/curatedRuleGuides.js'

test('all production curated guides satisfy evidence and semantic contracts', () => {
  for (const { slug, guide } of listCuratedRuleGuides()) {
    const result = validateRuleGuide(guide)
    expect(result.errors, `${slug}: ${result.errors.join(', ')}`).toEqual([])
    expect(getCuratedRuleGuide(slug)).not.toBeNull()
  }
})

test('structured curated games are not exposed as runtime quick-rule guides', () => {
  expect(getCuratedRuleGuide('skull-king')).toBeNull()
  expect(getCuratedRuleGuide('ipso')).toBeNull()
  expect(getCuratedRuleGuide('minna-de-ponkotsu-paint')).toBeNull()
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

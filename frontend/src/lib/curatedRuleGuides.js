const GUIDES = {}

export function validateRuleGuide(guide) {
  const errors = []

  if (!guide || guide.reviewed !== true) errors.push('guide is not reviewed')
  if (!guide?.ruleVersion) errors.push('ruleVersion is required')
  if (!guide?.source?.url?.startsWith('https://')) errors.push('https source URL is required')
  if (!guide?.source?.ruleVersion) errors.push('source ruleVersion is required')
  if (guide?.ruleVersion && guide?.source?.ruleVersion && guide.ruleVersion !== guide.source.ruleVersion) {
    errors.push('guide/source ruleVersion mismatch')
  }
  if (!Array.isArray(guide?.quick?.turnSteps) || guide.quick.turnSteps.length === 0) {
    errors.push('turnSteps are required')
  }
  if (!guide?.quick?.end) errors.push('end summary is required')
  if (!Array.isArray(guide?.flow) || guide.flow.length < 2) errors.push('flow requires at least two nodes')

  const actionCount = guide?.facts?.actionCount
  if (Number.isInteger(actionCount)) {
    if (!Array.isArray(guide?.quick?.actions) || guide.quick.actions.length !== actionCount) {
      errors.push(`action count mismatch: expected ${actionCount}`)
    }
  }

  const endThreshold = guide?.facts?.endThreshold
  if (Number.isInteger(endThreshold) && !String(guide?.quick?.end || '').includes(String(endThreshold))) {
    errors.push(`end threshold ${endThreshold} missing from summary`)
  }

  return { valid: errors.length === 0, errors }
}

export function getCuratedRuleGuide(slug) {
  const guide = GUIDES[slug]
  if (!guide) return null
  return validateRuleGuide(guide).valid ? guide : null
}

export function listCuratedRuleGuides() {
  return Object.entries(GUIDES).map(([slug, guide]) => ({ slug, guide }))
}

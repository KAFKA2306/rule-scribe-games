const FOCUSABLE_SELECTOR = [
  'button:not([disabled])',
  'a[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

function visibleFocusableElements(container) {
  return [...container.querySelectorAll(FOCUSABLE_SELECTOR)].filter((element) => {
    const style = window.getComputedStyle(element)
    return style.display !== 'none' && style.visibility !== 'hidden'
  })
}

export function installMobileFilterFocus() {
  let trigger = null

  const dialog = () => document.querySelector('#directory-filters.mobile-open')

  const restoreTriggerFocus = () => {
    window.requestAnimationFrame(() => {
      const filters = document.getElementById('directory-filters')
      filters?.removeAttribute('role')
      filters?.removeAttribute('aria-modal')
      trigger?.focus()
    })
  }

  document.addEventListener('click', (event) => {
    const toggle = event.target.closest('.mobile-filter-toggle')
    if (toggle) {
      trigger = toggle
      window.requestAnimationFrame(() => {
        const filters = dialog()
        if (!filters) return
        filters.setAttribute('role', 'dialog')
        filters.setAttribute('aria-modal', 'true')
        visibleFocusableElements(filters)[0]?.focus()
      })
      return
    }

    if (event.target.closest('.mobile-filter-close, .mobile-filter-backdrop')) restoreTriggerFocus()
  })

  document.addEventListener('keydown', (event) => {
    const filters = dialog()
    if (!filters) return

    if (event.key === 'Escape') {
      event.preventDefault()
      filters.querySelector('.mobile-filter-close')?.click()
      return
    }

    if (event.key !== 'Tab') return
    const focusable = visibleFocusableElements(filters)
    if (focusable.length === 0) {
      event.preventDefault()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  })
}

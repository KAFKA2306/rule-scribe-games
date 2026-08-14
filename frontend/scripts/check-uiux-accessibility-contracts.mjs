import { readFileSync } from 'node:fs'

const files = {
  app: readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8'),
  shell: readFileSync(new URL('../src/components/AppShell.jsx', import.meta.url), 'utf8'),
  modal: readFileSync(new URL('../src/components/EditGameModal.jsx', import.meta.url), 'utf8'),
}

const requirements = [
  ['mobile filter toggle', files.app, /aria-controls="directory-filters"/],
  ['explicit directory search label', files.app, /htmlFor="game-directory-search"/],
  ['explicit sort label', files.app, /htmlFor="game-sort"/],
  ['explicit AI generation CTA', files.app, /未登録ゲームをAIで追加/],
  ['compare pressed state', files.app, /aria-pressed=\{selected\}/],
  ['compare limit state', files.app, /比較できるゲームは3件まで/],
  ['tab right-arrow keyboard support', files.shell, /ArrowRight/],
  ['tab roving tabindex', files.shell, /tab\.tabIndex = tab === activeTab \? 0 : -1/],
  ['tab panel semantics', files.shell, /setAttribute\('role', 'tabpanel'\)/],
  ['modal dialog role', files.modal, /role="dialog"/],
  ['modal aria-modal', files.modal, /aria-modal="true"/],
  ['modal labelledby', files.modal, /aria-labelledby="edit-game-dialog-title"/],
  ['modal focus trap', files.modal, /focusableElements\(dialogRef\.current\)/],
  ['modal Escape close', files.modal, /event\.key === 'Escape'/],
  ['modal focus return', files.modal, /previousFocusRef/],
  ['explicit modal field labels', files.modal, /htmlFor="edit-game-title"/],
]

const failures = requirements.filter(([, source, pattern]) => !pattern.test(source)).map(([name]) => name)
if (failures.length > 0) {
  console.error(`UI/UX accessibility contract failures:\n- ${failures.join('\n- ')}`)
  process.exit(1)
}

console.log(`UI/UX accessibility contracts: ${requirements.length} checks passed`)

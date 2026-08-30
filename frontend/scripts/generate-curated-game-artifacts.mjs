import { createHash } from 'node:crypto'
import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')
const repoRoot = path.resolve(frontendRoot, '..')
const curatedDir = path.join(repoRoot, 'data', 'curated-games')
const deploymentManifestPath = path.join(frontendRoot, 'public', 'curated-guides-manifest.json')

async function writeIfChanged(filePath, content) {
  let current = null
  try {
    current = await readFile(filePath, 'utf8')
  } catch {
    current = null
  }
  if (current === content) return
  await mkdir(path.dirname(filePath), { recursive: true })
  await writeFile(filePath, content, 'utf8')
}

async function loadSpecs() {
  const names = (await readdir(curatedDir))
    .filter((name) => name.endsWith('.json') && !name.startsWith('schema-'))
    .sort()

  const specs = []
  for (const name of names) {
    const raw = await readFile(path.join(curatedDir, name), 'utf8')
    const spec = JSON.parse(raw)
    const stem = name.slice(0, -'.json'.length)
    if (!spec.slug || stem !== spec.slug) {
      throw new Error(`curated spec filename/slug mismatch: ${name}`)
    }
    if (!spec.source?.rule_version || !spec.source?.revision) {
      throw new Error(`curated source revision contract missing: ${name}`)
    }
    specs.push(spec)
  }
  return specs
}

function renderManifest(specs) {
  const games = Object.fromEntries(
    specs.map((spec) => [
      spec.slug,
      {
        rule_version: spec.source.rule_version,
        source_revision: spec.source.revision,
      },
    ]),
  )
  const revisionContract = JSON.stringify(games)
  const digest = createHash('sha256').update(revisionContract, 'utf8').digest('hex')
  return `${JSON.stringify(
    {
      games,
      revision_contract_sha256: digest,
      schema_version: 1,
    },
    null,
    2,
  )}\n`
}

const specs = await loadSpecs()
await writeIfChanged(deploymentManifestPath, renderManifest(specs))
console.log(`curated manifest generated: ${specs.length} game(s)`)

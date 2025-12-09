import { createClient } from '@supabase/supabase-js'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import dotenv from 'dotenv'

// Load environment variables from .env file in project root
// We need to look up two levels from frontend/scripts/ to root
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const rootDir = path.resolve(__dirname, '../../')

// Try loading from root .env
dotenv.config({ path: path.join(rootDir, '.env') })

// Fallback: try loading from frontend .env if exists (though usually it's in root for monorepos/this specific structure)
dotenv.config({ path: path.join(__dirname, '../.env') })

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY
const PUBLIC_URL = 'https://bodoge-no-mikata.vercel.app'

async function generateSitemap() {
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    console.error('Error: Supabase environment variables are missing.')
    // In CI/Build environments, we might want to fallback or fail.
    // For now, let's fail to ensure we know something is wrong,
    // unless it's strictly build-time without envs (which shouldn't happen for sitemap gen).
    process.exit(1)
  }

  console.log('Generating sitemap...')
  console.log(`Using Supabase URL: ${SUPABASE_URL}`)

  const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

  // Fetch all games
  const { data: games, error } = await supabase
    .from('games')
    .select('slug, updated_at, title, title_ja, image_url')

  if (error) {
    console.error('Error fetching games:', error)
    process.exit(1)
  }

  console.log(`Found ${games.length} games.`)

  const sitemapContent = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>${PUBLIC_URL}/</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>${PUBLIC_URL}/data</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
${games
  .map((game) => {
    const lastMod = game.updated_at
      ? game.updated_at.split('T')[0]
      : new Date().toISOString().split('T')[0]
    const title = game.title_ja || game.title || game.slug
    const imageUrl = game.image_url || `${PUBLIC_URL}/assets/games/${game.slug}.png`
    return `  <url>
    <loc>${PUBLIC_URL}/games/${game.slug}</loc>
    <lastmod>${lastMod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
    <image:image>
      <image:loc>${imageUrl}</image:loc>
      <image:title>${title}</image:title>
    </image:image>
  </url>`
  })
  .join('\n')}
</urlset>`

  const outputPath = path.join(__dirname, '../public/sitemap.xml')
  fs.writeFileSync(outputPath, sitemapContent)
  console.log(`Sitemap generated at ${outputPath}`)
}

generateSitemap().catch((err) => {
  console.error(err)
  process.exit(1)
})

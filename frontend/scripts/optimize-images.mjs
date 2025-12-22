import sharp from 'sharp';
import { readdirSync, existsSync, unlinkSync } from 'fs';
import { join, basename, extname } from 'path';

const publicDir = 'public';
const assetsDir = join(publicDir, 'assets');
const gamesDir = join(assetsDir, 'games');

async function optimizeImage(inputPath, outputPath, options = {}) {
  const { width, height, quality = 80 } = options;
  
  let pipeline = sharp(inputPath);
  
  if (width || height) {
    pipeline = pipeline.resize(width, height, { fit: 'inside', withoutEnlargement: true });
  }
  
  await pipeline.webp({ quality }).toFile(outputPath);
  
  console.log(`✓ ${basename(inputPath)} → ${basename(outputPath)}`);
}

async function main() {
  console.log('🚀 Starting image optimization...\n');

  await optimizeImage(
    join(publicDir, 'favicon.png'),
    join(publicDir, 'favicon.webp'),
    { width: 64, height: 64, quality: 90 }
  );

  await optimizeImage(
    join(publicDir, 'og-image.png'),
    join(publicDir, 'og-image.webp'),
    { width: 1200, height: 630, quality: 85 }
  );

  await optimizeImage(
    join(assetsDir, 'header-icon.png'),
    join(assetsDir, 'header-icon.webp'),
    { width: 128, height: 128, quality: 85 }
  );

  await optimizeImage(
    join(assetsDir, 'empty-meeple.png'),
    join(assetsDir, 'empty-meeple.webp'),
    { width: 400, height: 400, quality: 80 }
  );

  await optimizeImage(
    join(assetsDir, 'thinking-meeple.png'),
    join(assetsDir, 'thinking-meeple.webp'),
    { width: 400, height: 400, quality: 80 }
  );

  const pngFiles = readdirSync(gamesDir).filter(f => f.endsWith('.png'));
  console.log(`\n📦 Converting ${pngFiles.length} game images...\n`);
  
  for (const file of pngFiles) {
    const inputPath = join(gamesDir, file);
    const outputPath = join(gamesDir, file.replace('.png', '.webp'));
    
    await optimizeImage(inputPath, outputPath, { width: 800, quality: 80 });
  }

  console.log('\n✅ Image optimization complete!');
}

main();

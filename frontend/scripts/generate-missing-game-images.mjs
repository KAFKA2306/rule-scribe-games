import { createHash } from 'node:crypto'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import sharp from 'sharp'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')
const outputDir = path.join(frontendRoot, 'public', 'images', 'games', 'generated')

const games = [
  { slug: "3", title: "3秒トライ！" },
  { slug: "3-second-try", title: "3秒トライ！" },
  { slug: "age-of-steam", title: "蒸気の時代" },
  { slug: "asahi-ecomuseum-karuta", title: "朝日町エコミュージアムかるた" },
  { slug: "azul-summer-pavilion", title: "アズール：サマーパビリオン" },
  { slug: "big-shot", title: "ビッグショット" },
  { slug: "bob-jiten", title: "ボブジテン" },
  { slug: "bob-jiten-kids", title: "ボブジテンきっず" },
  { slug: "bounce-off", title: "バウンス・オフ！" },
  { slug: "brass-birmingham", title: "ブラス：バーミンガム" },
  { slug: "brass-lancashire", title: "ブラス：ランカシャー" },
  { slug: "calico", title: "キャリコ" },
  { slug: "candy-land-sweet-land", title: "スウィートランド (キャンディランド)" },
  { slug: "castles-of-mad-king-ludwig", title: "ノイシュヴァンシュタイン城" },
  { slug: "cat-and-chocolate-daily-mystery", title: "キャット＆チョコレート：日常編" },
  { slug: "clank", title: "クランク！" },
  { slug: "clans-of-caledonia", title: "クランズ・オブ・カレドニア" },
  { slug: "coup", title: "クー" },
  { slug: "detective-conan-karuta", title: "名探偵コナン 名台詞かるた" },
  { slug: "electropolis", title: "電力世界" },
  { slug: "fab-fib", title: "ファブフィブ" },
  { slug: "fixer", title: "フィクサー" },
  { slug: "flip-7-with-a-vengeance", title: "フリップ7:ウィズ・ア・ベンジェンス" },
  { slug: "font-karuta", title: "フォントかるた" },
  { slug: "for-sale", title: "フォーセール" },
  { slug: "gambler-x-gamble", title: "ギャンブラー×ギャンブル！" },
  { slug: "game", title: "みんなでぽんこつペイント" },
  { slug: "gizmos", title: "ギズモ" },
  { slug: "icefall", title: "アイスフォール" },
  { slug: "istanbul-choose-and-write", title: "Istanbul: Choose & Write" },
  { slug: "istanbul-dice-game", title: "Istanbul: The Dice Game" },
  { slug: "just-one", title: "ジャストワン" },
  { slug: "kokushoujaku", title: "黒召雀" },
  { slug: "little-town-builders", title: "リトルタウンビルダーズ" },
  { slug: "lost-ruins-of-arnak", title: "アルナックの失われし遺跡" },
  { slug: "mahjong-generic", title: "麻雀" },
  { slug: "maimajo", title: "マイマジョ (Mai Majo)" },
  { slug: "marrakech", title: "マラケシュ" },
  { slug: "modern-art", title: "モダンアート" },
  { slug: "not-my-fault", title: "ノットマイフォルト" },
  { slug: "orapa-mine", title: "オラパマイン" },
  { slug: "paris", title: "パリ" },
  { slug: "pictures", title: "ピクチャーズ" },
  { slug: "pili-pili", title: "ピリピリ" },
  { slug: "quick-shot", title: "クイックショット！" },
  { slug: "raise-your-goblets", title: "ワインと毒とゴブレット" },
  { slug: "relative-space", title: "レラティブ・スペース" },
  { slug: "sea-turtle-soup", title: "ウミガメのスープ" },
  { slug: "secret-hitler", title: "シークレットヒトラー" },
  { slug: "skull-king", title: "スカルキング" },
  { slug: "slide", title: "スライド" },
  { slug: "splendor", title: "宝石の煌き" },
  { slug: "taverns-of-tiefenthal", title: "ティーフェンタールの酒場" },
  { slug: "tea-garden", title: "ティーガーデン" },
  { slug: "terraforming-mars-the-dice-game", title: "テラフォーミング・マーズ ダイスゲーム" },
  { slug: "thats-not-a-hat", title: "ザッツ・ノット・ア・ハット" },
  { slug: "todai-nanja-monja", title: "東大ナンジャモンジャ" },
  { slug: "trapwords", title: "トラップワード" },
  { slug: "tricky-sound", title: "Tricky Sound (トリッキー・サウンド)" },
  { slug: "ubongo", title: "ウボンゴ" },
  { slug: "unlock", title: "アンロック！" },
  { slug: "via-nebula", title: "ヴィア・ネビュラ" },
  { slug: "viticulture", title: "ワイナリーの四季" },
  { slug: "we-didnt-playtest-this-at-all", title: "テストプレイなんてしてないよ" },
  { slug: "web-of-power", title: "王と枢機卿" },
  { slug: "white-castle-matcha", title: "白鷺城／ホワイト・キャッスル ＋ 茶の湯" },
  { slug: "wyrmspan", title: "ワイアームスパン" },
  { slug: "yro", title: "YRO" },
]

function hashBytes(value) {
  return createHash('sha256').update(value).digest()
}

function palette(slug) {
  const hash = hashBytes(slug)
  const hue = (hash[0] / 255) * 360
  const hue2 = (hue + 35 + (hash[1] % 90)) % 360
  const hue3 = (hue + 165 + (hash[2] % 70)) % 360
  return {
    a: `hsl(${hue.toFixed(0)} 58% 44%)`,
    b: `hsl(${hue2.toFixed(0)} 66% 55%)`,
    c: `hsl(${hue3.toFixed(0)} 54% 36%)`,
  }
}

function xmlEscape(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

function motifFor(slug) {
  if (/(mars|space|nebula)/.test(slug)) return 'space'
  if (/(castle|paris|istanbul|power|brass|steam|web-of-power)/.test(slug)) return 'city'
  if (/(karuta|bob-jiten|trapwords|just-one|font)/.test(slug)) return 'words'
  if (/(dice|gizmos|mahjong|kokushoujaku)/.test(slug)) return 'tiles'
  if (/(wine|viticulture|taverns|goblets|tea-garden|marrakech)/.test(slug)) return 'garden'
  if (/(sea|skull|wyrm|calico|cat-and-chocolate|maimajo)/.test(slug)) return 'creature'
  if (/(bounce|slide|ubongo|quick-shot|flip-7|3-second|^3$)/.test(slug)) return 'action'
  if (/(ruins|mine|unlock|clank)/.test(slug)) return 'adventure'
  return 'cards'
}

function renderMotif(slug, colors) {
  const hash = hashBytes(slug)
  const motif = motifFor(slug)
  if (motif === 'space') {
    const stars = Array.from({ length: 46 }, (_, index) => {
      const x = (hash[index % hash.length] * (index + 17) * 13) % 800
      const y = (hash[(index + 7) % hash.length] * (index + 11) * 7) % 390
      const r = 1 + (hash[(index + 13) % hash.length] % 3)
      return `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff9" />`
    }).join('')
    return `${stars}<circle cx="590" cy="190" r="118" fill="${colors.b}" opacity=".92"/><circle cx="590" cy="190" r="153" fill="none" stroke="#fff9" stroke-width="9"/><path d="M120 335 Q390 120 720 285" fill="none" stroke="${colors.a}" stroke-width="18" stroke-linecap="round"/>`
  }
  if (motif === 'city') {
    return `<g opacity=".96">
      <rect x="70" y="225" width="105" height="205" rx="8" fill="${colors.a}"/>
      <rect x="195" y="145" width="120" height="285" rx="8" fill="${colors.b}"/>
      <rect x="335" y="250" width="95" height="180" rx="8" fill="${colors.c}"/>
      <rect x="450" y="105" width="135" height="325" rx="8" fill="${colors.a}"/>
      <rect x="605" y="195" width="115" height="235" rx="8" fill="${colors.b}"/>
      <path d="M400 80 L500 185 L300 185 Z" fill="#fff8"/>
    </g>`
  }
  if (motif === 'words') {
    const labels = ['A', '?', '字', 'Q', 'あ', 'Z', '言', 'ボ']
    return labels.map((label, index) => {
      const x = 65 + (index % 4) * 185
      const y = 75 + Math.floor(index / 4) * 150
      const fill = [colors.a, colors.b, colors.c][index % 3]
      return `<rect x="${x}" y="${y}" width="145" height="110" rx="18" fill="${fill}" stroke="#fff8" stroke-width="4"/><text x="${x + 72}" y="${y + 75}" text-anchor="middle" font-size="54" font-family="sans-serif" fill="white">${xmlEscape(label)}</text>`
    }).join('')
  }
  if (motif === 'tiles') {
    return Array.from({ length: 12 }, (_, index) => {
      const x = 65 + (index % 6) * 118
      const y = 70 + Math.floor(index / 6) * 160
      const dots = 1 + (hash[index] % 6)
      const circles = Array.from({ length: dots }, (_, dot) => {
        const cx = x + 28 + (dot % 3) * 30
        const cy = y + 38 + Math.floor(dot / 3) * 38
        return `<circle cx="${cx}" cy="${cy}" r="9" fill="${[colors.a, colors.b, colors.c][dot % 3]}"/>`
      }).join('')
      return `<rect x="${x}" y="${y}" width="92" height="125" rx="13" fill="#fffde9" stroke="#fff8" stroke-width="3"/>${circles}`
    }).join('')
  }
  if (motif === 'garden') {
    const flowers = Array.from({ length: 34 }, (_, index) => {
      const x = 55 + ((hash[index % hash.length] * (index + 5) * 17) % 690)
      const y = 65 + ((hash[(index + 9) % hash.length] * (index + 3) * 11) % 335)
      const r = 11 + (hash[(index + 5) % hash.length] % 25)
      const fill = [colors.a, colors.b, colors.c][index % 3]
      return `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" opacity=".88"/>`
    }).join('')
    return `${flowers}<path d="M120 390 Q310 180 430 370 T720 270" fill="none" stroke="#fff9" stroke-width="10"/>`
  }
  if (motif === 'creature') {
    return `<circle cx="400" cy="245" r="170" fill="${colors.b}" opacity=".94"/>
      <path d="M270 130 L315 45 L360 145 Z M440 145 L500 45 L545 140 Z" fill="${colors.b}"/>
      <circle cx="345" cy="215" r="34" fill="white"/><circle cx="455" cy="215" r="34" fill="white"/>
      <circle cx="345" cy="215" r="13" fill="${colors.c}"/><circle cx="455" cy="215" r="13" fill="${colors.c}"/>
      <path d="M325 295 Q400 350 485 285" fill="none" stroke="${colors.c}" stroke-width="12" stroke-linecap="round"/>`
  }
  if (motif === 'action') {
    const balls = Array.from({ length: 11 }, (_, index) => {
      const x = 85 + index * 62
      const y = 235 + Math.sin(index * .8) * 92
      const fill = [colors.a, colors.b, colors.c][index % 3]
      return `<circle cx="${x}" cy="${y.toFixed(1)}" r="24" fill="${fill}" stroke="#fff" stroke-width="4"/>`
    }).join('')
    return `${balls}<path d="M85 390 L715 95" stroke="#fff" stroke-width="10" stroke-linecap="round"/><path d="M715 95 L658 105 L690 152 Z" fill="#fff"/>`
  }
  if (motif === 'adventure') {
    return `<path d="M80 410 L245 155 L400 410 Z" fill="${colors.c}"/><path d="M255 410 L475 80 L705 410 Z" fill="${colors.b}"/><path d="M550 410 L690 185 L770 410 Z" fill="${colors.a}"/><path d="M135 385 Q350 305 690 190" fill="none" stroke="#ffe699" stroke-width="10" stroke-dasharray="15 18"/>`
  }
  return Array.from({ length: 7 }, (_, index) => {
    const x = 65 + index * 96
    const y = 95 + (index % 2) * 70
    const rotate = -18 + index * 6
    const fill = index % 2 === 0 ? '#fffdf2' : [colors.a, colors.b, colors.c][index % 3]
    return `<g transform="rotate(${rotate} ${x + 62} ${y + 95})"><rect x="${x}" y="${y}" width="124" height="190" rx="17" fill="${fill}" stroke="#fff9" stroke-width="5"/><circle cx="${x + 62}" cy="${y + 95}" r="28" fill="${[colors.a, colors.b, colors.c][index % 3]}"/></g>`
  }).join('')
}

function renderSvg(game) {
  const colors = palette(game.slug)
  const motif = renderMotif(game.slug, colors)
  const label = xmlEscape(game.slug.toUpperCase().replaceAll('-', ' '))
  return `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="${colors.c}"/>
        <stop offset=".52" stop-color="${colors.a}"/>
        <stop offset="1" stop-color="${colors.b}"/>
      </linearGradient>
      <radialGradient id="glow" cx=".2" cy=".1" r=".9">
        <stop offset="0" stop-color="#fff" stop-opacity=".27"/>
        <stop offset="1" stop-color="#fff" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <rect width="800" height="600" fill="url(#bg)"/>
    <rect width="800" height="600" fill="url(#glow)"/>
    <g>${motif}</g>
    <rect x="28" y="470" width="744" height="102" rx="22" fill="#0d1527" fill-opacity=".9" stroke="#fff" stroke-opacity=".55" stroke-width="2"/>
    <text x="58" y="510" font-family="sans-serif" font-size="17" letter-spacing="2.2" fill="#dce6f3">GENERATED CATALOG ART</text>
    <text x="58" y="550" font-family="sans-serif" font-size="27" font-weight="700" fill="white">${label.slice(0, 42)}</text>
  </svg>`
}

await mkdir(outputDir, { recursive: true })

for (const game of games) {
  const svg = renderSvg(game)
  const outputPath = path.join(outputDir, `${game.slug}.webp`)
  await sharp(Buffer.from(svg)).webp({ quality: 82, effort: 5 }).toFile(outputPath)
}

console.log(`generated catalog images: ${games.length} game(s) -> ${path.relative(frontendRoot, outputDir)}`)

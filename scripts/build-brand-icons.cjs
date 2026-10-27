// Render the existing SVG logo; no new logo artwork is generated here.
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require(process.env.SHARP_MODULE || 'sharp');
const root = path.resolve(__dirname, '..');
(async () => {
  const svg = await fs.readFile(path.join(root, 'static/brand/daniel-monogram.svg'), 'utf8');
  const out = path.join(root, 'static/pwa');
  await fs.mkdir(out, { recursive: true });
  for (const size of [192, 512]) {
    await sharp(Buffer.from(svg)).resize(size, size).png().toFile(path.join(out, `icon-${size}.png`));
    // Keep the full monogram inside the maskable icon's central safe zone.
    const inner = svg.replace('<svg ', '<svg x="96" y="96" width="320" height="320" ');
    const mask = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" fill="#123B34"/>${inner}</svg>`;
    await sharp(Buffer.from(mask)).resize(size, size).png().toFile(path.join(out, `maskable-${size}.png`));
  }
  await sharp(Buffer.from(svg)).resize(180, 180).flatten({ background: '#123B34' }).png().toFile(path.join(out, 'apple-touch-icon.png'));
  await sharp(Buffer.from(svg)).resize(32, 32).png().toFile(path.join(out, 'favicon-32.png'));
  await sharp(path.join(root, 'static/brand/social-card.svg')).png().toFile(path.join(root, 'static/brand/social-card.png'));
  console.log('Created six PNG icons and the social sharing image.');
})();

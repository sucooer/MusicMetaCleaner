import playwright from '/tmp/mmc-playwright/node_modules/playwright/index.js';

const { chromium } = playwright;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.goto('http://127.0.0.1:5000', { waitUntil: 'networkidle' });

const bodyText = await page.locator('body').innerText();
if (bodyText.includes('{{ uiMode') || bodyText.includes('[[ uiMode')) {
  throw new Error('Vue interpolation was not rendered');
}

await page.getByRole('button', { name: /展开设置|收起设置/ }).click();
const keywordLabel = await page.locator('text=关键词规则').isVisible();
if (!keywordLabel) {
  throw new Error('Settings panel did not expand');
}

await browser.close();
console.log('playwright e2e ok');

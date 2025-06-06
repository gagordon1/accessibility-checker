// Stage‑1 WCAG crawler ‑‑ TypeScript version
// -------------------------------------------------------------
// Requirements (Node ≥18):
//   npm install puppeteer axe-core yargs fs-extra
//   npm install -D ts-node typescript @types/node @types/fs-extra @types/yargs
// Usage examples:
//   npx ts-node stage1_crawler.ts --start https://example.gov --maxPages 50 --output results.json
//   npx ts-node stage1_crawler.ts -s https://agency.gov -d agency.gov -o scans.json
//
// Flags:
//   --start / -s     Starting URL (seed page)
//   --domain / -d    (Optional) restrict crawl to this domain; defaults to seed host
//   --maxPages / -m  Maximum pages to scan (default 100)
//   --output / -o    Output JSON path (default wcag_scan.json)
//
// Notes:
// * Written in TypeScript for stronger typing + IntelliSense.
// * Performs a breadth‑first crawl within the specified domain, renders pages
//   in headless Chromium via Puppeteer, injects axe‑core, and records WCAG 2.1 AA
//   violations.  Produces a lightweight JSON array suitable for piping into
//   Step‑2 (Python LLM analysis).
// -------------------------------------------------------------

import fs from 'fs-extra';
import path from 'path';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import puppeteer, { Browser, Page } from 'puppeteer';
import { source as axeSource } from 'axe-core';
import { URL } from 'url';

interface AxeNodeResult {
  html: string;
  target: string[];
  failureSummary: string;
}

interface AxeViolation {
  id: string;
  impact?: string;
  description?: string;
  nodes: AxeNodeResult[];
}

interface PageResult {
  url: string;
  timestamp: string;
  violations?: AxeViolation[];
  error?: string;
}

// ------------------------ CLI args ----------------------------------------
const argv = yargs(hideBin(process.argv))
  .option('start', {
    alias: 's',
    demandOption: true,
    describe: 'Seed URL to start crawling',
    type: 'string',
  })
  .option('domain', {
    alias: 'd',
    describe: 'Restrict crawl to this domain; defaults to seed host',
    type: 'string',
  })
  .option('maxPages', {
    alias: 'm',
    default: 100,
    describe: 'Maximum number of pages to scan',
    type: 'number',
  })
  .option('output', {
    alias: 'o',
    default: 'wcag_scan.json',
    describe: 'Path to write JSON results',
    type: 'string',
  })
  .help()
  .argv as unknown as {
    start: string;
    domain?: string;
    maxPages: number;
    output: string;
  };

// ------------------------ helpers -----------------------------------------
function normalizeUrl(rawUrl: string): string | null {
  try {
    const url = new URL(rawUrl);
    url.hash = '';
    return url.href;
  } catch {
    return null;
  }
}

function isSameDomain(url: string, baseDomain: string): boolean {
  try {
    return new URL(url).hostname.endsWith(baseDomain);
  } catch {
    return false;
  }
}

async function extractLinks(page: Page, baseDomain: string): Promise<string[]> {
  const hrefs = await page.$$eval('a[href]', (anchors) => anchors.map((a) => (a as HTMLAnchorElement).href));
  const links = new Set<string>();
  hrefs.forEach((href) => {
    const clean = normalizeUrl(href);
    if (clean && isSameDomain(clean, baseDomain)) links.add(clean);
  });
  return Array.from(links);
}

async function runAxe(page: Page): Promise<AxeViolation[]> {
  // Inject axe‐core if not already present
  await page.evaluate(axeSource);
  const result = await page.evaluate(async () => {
    // @ts-ignore – axe is injected in the page context
    return await (window as any).axe.run({
      runOnly: {
        type: 'tag',
        values: ['wcag2aa', 'wcag21aa'],
      },
    });
  });
  return result.violations as AxeViolation[];
}

// ------------------------ main crawler ------------------------------------
(async () => {
  const seedUrl = normalizeUrl(argv.start);
  if (!seedUrl) {
    console.error('Invalid seed URL.');
    process.exit(1);
  }

  const baseDomain = argv.domain || new URL(seedUrl).hostname;
  const maxPages = argv.maxPages;

  const queue: string[] = [seedUrl];
  const visited: Set<string> = new Set();
  const results: PageResult[] = [];

  const browser: Browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page: Page = await browser.newPage();
  page.setDefaultNavigationTimeout(45000);

  while (queue.length && visited.size < maxPages) {
    const url = queue.shift() as string;
    if (visited.has(url)) continue;
    visited.add(url);
    console.log(`Scanning (${visited.size}/${maxPages}): ${url}`);

    try {
      await page.goto(url, { waitUntil: 'networkidle2' });

      const violations = await runAxe(page);
      const record: PageResult = {
        url,
        timestamp: new Date().toISOString(),
        violations: violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          description: v.description,
          nodes: v.nodes.map((n) => ({
            html: n.html,
            target: n.target,
            failureSummary: n.failureSummary,
          })),
        })),
      };
      results.push(record);

      const newLinks = await extractLinks(page, baseDomain);
      newLinks.forEach((link) => {
        const clean = normalizeUrl(link);
        if (
          clean &&
          !visited.has(clean) &&
          !queue.includes(clean) &&
          queue.length < maxPages
        ) {
          queue.push(clean);
        }
      });
    } catch (err: any) {
      results.push({ url, timestamp: new Date().toISOString(), error: err.message });
      console.error(`Error scanning ${url}: ${err.message}`);
    }
  }

  await browser.close();

  await fs.outputJson(path.resolve(argv.output), results, { spaces: 2 });
  console.log(`\n✔ Scan complete. Results saved to ${argv.output}`);
})();

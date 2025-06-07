// ---------------------------------------------------------------------------
// Stage‑1 WCAG Crawler — MODULAR Tiered Version (TypeScript)
// ---------------------------------------------------------------------------
//  ✅ Drop‑in replacement for your previous stage1_crawler.ts
//  ✅ Axe‑core baseline + plug‑and‑play bespoke rules per WCAG criterion
//  ✅ Tier flag (-t basic|standard|premium) chooses rule bundles
// ---------------------------------------------------------------------------
// Install deps (Node ≥18):
//   npm install puppeteer axe-core yargs fs-extra
//   npm install -D ts-node typescript @types/node @types/fs-extra @types/yargs
// ---------------------------------------------------------------------------
// Run examples:
//   npx ts-node stage1_crawler_modular.ts -s https://example.gov -t basic   
//   npx ts-node stage1_crawler_modular.ts -s https://example.gov -t premium -m 50
// ---------------------------------------------------------------------------

// -------------------- imports ------------------------------------------------
import fs from "fs-extra";
import path from "path";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import puppeteer, { Browser, Page } from "puppeteer";
import { URL } from "url";
import { tiers, TierName, PageResult } from "./rules";


const argv = yargs(hideBin(process.argv))
  .option("start", { alias: "s", demandOption: true, type: "string", describe: "Seed URL" })
  .option("domain", { alias: "d", type: "string", describe: "Restrict crawl to this domain" })
  .option("maxPages", { alias: "m", type: "number", default: 100, describe: "Max pages" })
  .option("output", { alias: "o", type: "string", default: "scans/wcag_scan.json", describe: "Output JSON" })
  .option("tier", {
    alias: "t",
    default: "basic",
    choices: Object.keys(tiers),
    describe: "Compliance tier (rule bundle)",
  })
  .help()
  .argv as unknown as {
    start: string;
    domain?: string;
    maxPages: number;
    output: string;
    tier: TierName;
  };

// -------------------- helpers ---------------------------------------------
function normalizeUrl(raw: string): string | null {
  try {
    const u = new URL(raw);
    u.hash = "";
    // Remove www. prefix if it exists
    if (u.hostname.startsWith('www.')) {
      u.hostname = u.hostname.slice(4);
    }
    return u.href;
  } catch {
    return null;
  }
}

function sameDomain(url: string, base: string) {
  try {
    const urlHost = new URL(url).hostname;
    const baseHost = new URL(base).hostname;
    return urlHost === baseHost || urlHost.endsWith('.' + baseHost);
  } catch {
    return false;
  }
}

async function extractLinks(page: Page, base: string) {
  const hrefs = await page.$$eval("a[href]", (a) => a.map((n) => (n as HTMLAnchorElement).href));
  const set = new Set<string>();
  hrefs.forEach((h) => {
    const clean = normalizeUrl(h);
    if (clean && sameDomain(clean, base)) set.add(clean);
  });
  return Array.from(set);
}

// -------------------- main crawler ----------------------------------------
(async () => {
  const seed = normalizeUrl(argv.start);
  if (!seed) throw new Error("Invalid seed URL");

  const domain = argv.domain || new URL(seed).hostname;
  const max = argv.maxPages;
  const activeRules = tiers[argv.tier];

  const queue: string[] = [seed];
  const visited = new Set<string>();
  const results: PageResult[] = [];

  const browser: Browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox"] });
  const page: Page = await browser.newPage();
  page.setDefaultNavigationTimeout(45000);

  while (queue.length && visited.size < max) {
    const url = queue.shift() as string;
    if (visited.has(url)) continue;
    visited.add(url);
    console.log(`Scanning (${visited.size}/${max}): ${url}`);

    try {
      await page.goto(url, { waitUntil: "networkidle2" });

      // run all rule functions then flatten
      // const violations = (await Promise.all(activeRules.map((fn) => fn(page)))).flat();

      // results.push({ url, timestamp: new Date().toISOString(), violations });

      const newLinks = await extractLinks(page, domain);
      newLinks.forEach((l) => {
        if (visited.size + queue.length >= max) return;
        const clean = normalizeUrl(l);
        if (clean && !visited.has(clean) && !queue.includes(clean)) {
          // Double check we haven't already queued this URL
          if (!queue.some(q => normalizeUrl(q) === clean)) {
            queue.push(clean);
          }
        }
      });
    } catch (err: any) {
      console.error(`Error scanning ${url}: ${err.message}`);
      results.push({ url, timestamp: new Date().toISOString(), violations: [], error: err.message });
    }
  }

  await browser.close();
  await fs.outputJson(path.resolve(argv.output), results, { spaces: 2 });
  console.log(`\n✔ Scan complete. Results saved to ${argv.output}`);
})();

// ---------------------------------------------------------------------------
// 👉 To add a new bespoke rule: create a new async function that matches
//    RuleFunction, push it into the desired tier array, and you're done.
// ---------------------------------------------------------------------------

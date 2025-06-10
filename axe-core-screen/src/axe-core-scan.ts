// ---------------------------------------------------------------------------
// Axe-Core WCAG Scanner - Single URL Version
// ---------------------------------------------------------------------------
// Simple axe-core scanner that runs accessibility checks on a single URL
// and saves the violations to a JSON file.
// ---------------------------------------------------------------------------
// Install deps (Node ≥18):
//   npm install puppeteer axe-core yargs fs-extra
//   npm install -D ts-node typescript @types/node @types/fs-extra @types/yargs
// ---------------------------------------------------------------------------
// Run example:
//   npx ts-node axe-core-scan.ts --url https://example.com --output results.json
// ---------------------------------------------------------------------------

import fs from "fs-extra";
import path from "path";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import puppeteer, { Browser, Page } from "puppeteer";
import { source as axeSource } from "axe-core";

// -------------------- shared types ------------------------------------------
export interface NodeResult {
  html: string;
  target: string[];
  failureSummary?: string;
}

export interface Violation {
  id: string; // WCAG id
  description: string;
  impact?: string; // minor|moderate|serious|critical
  nodes: NodeResult[];
}

export interface ScanResult {
  url: string;
  timestamp: string;
  violations: Violation[];
  error?: string;
}

// -------------------- Command line arguments --------------------------------
const argv = yargs(hideBin(process.argv))
  .option("url", {
    alias: "u",
    demandOption: true,
    type: "string",
    describe: "URL to scan for accessibility violations"
  })
  .option("output", {
    alias: "o",
    demandOption: true,
    type: "string",
    describe: "Output JSON file path"
  })
  .help()
  .argv as unknown as {
    url: string;
    output: string;
  };

// -------------------- Axe-core scanner function -----------------------------
async function runAxeScan(page: Page): Promise<Violation[]> {
  // Inject axe-core into the page
  await page.evaluate(axeSource);
  
  // Run axe-core accessibility checks
  const result = await page.evaluate(async () => {
    // @ts-ignore – axe injected globally
    return await (window as any).axe.run({
      runOnly: { type: "tag", values: ["wcag2aa", "wcag21aa", "wcag22aa"] },
    });
  });

  // Transform axe results to our format
  return (result.violations as any[]).map<Violation>((v) => ({
    id: v.id,
    description: v.description,
    impact: v.impact,
    nodes: v.nodes.map((n: any) => ({
      html: n.html,
      target: n.target,
      failureSummary: n.failureSummary,
    })),
  }));
}

// -------------------- Main scanner ------------------------------------------
(async () => {
  const url = argv.url;
  const outputPath = path.resolve(argv.output);

  console.log(`Scanning URL: ${url}`);
  console.log(`Output file: ${outputPath}`);

  const browser: Browser = await puppeteer.launch({ 
    headless: true, 
    args: ["--no-sandbox", "--disable-setuid-sandbox"] 
  });

  try {
    const page: Page = await browser.newPage();
    page.setDefaultNavigationTimeout(30000);

    // Navigate to the URL
      await page.goto(url, { waitUntil: "networkidle2" });

    // Run axe-core scan
    const violations = await runAxeScan(page);

    // Prepare results
    const result: ScanResult = {
      url,
      timestamp: new Date().toISOString(),
      violations,
    };

    // Ensure output directory exists
    await fs.ensureDir(path.dirname(outputPath));

    // Save results to JSON file
    await fs.writeJson(outputPath, result, { spaces: 2 });

    console.log(`✅ Scan complete!`);
    console.log(`Found ${violations.length} violations`);
    console.log(`Results saved to: ${outputPath}`);

  } catch (error: any) {
    console.error(`❌ Error scanning ${url}:`, error.message);
    
    // Save error result
    const errorResult: ScanResult = {
      url,
      timestamp: new Date().toISOString(),
      violations: [],
      error: error.message,
    };

    await fs.ensureDir(path.dirname(outputPath));
    await fs.writeJson(outputPath, errorResult, { spaces: 2 });
    
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
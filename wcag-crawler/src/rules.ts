// -------------------- shared types ------------------------------------------
import { Page } from "puppeteer";
import { source as axeSource } from "axe-core";

export interface NodeResult {
  html: string;
  target: string[];
  failureSummary?: string;
}

export interface Violation {
  id: string; // WCAG id or custom
  description: string;
  impact?: string; // minor|moderate|serious|critical
  nodes: NodeResult[];
}

export type RuleFunction = (page: Page) => Promise<Violation[]>;

export interface PageResult {
  url: string;
  timestamp: string;
  violations: Violation[];
  error?: string;
}

// -------------------- Rule: axe‑core wrapper --------------------------------
export const axeRule: RuleFunction = async (page) => {
  await page.evaluate(axeSource);
  const result = await page.evaluate(async () => {
    // @ts-ignore – axe injected
    return await (window as any).axe.run({
      runOnly: { type: "tag", values: ["wcag2aa", "wcag21aa"] },
    });
  });

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
};

// -------------------- Rule: 1.4.2 Audio Control -----------------------------
export const rule_1_4_2_audio: RuleFunction = async (page) => {
  const offenders = await page.evaluate(() => {
    return Array.from(document.querySelectorAll("audio, video"))
      .filter((el) => el.hasAttribute("autoplay") && !el.hasAttribute("controls"))
      .map((el) => el.outerHTML.slice(0, 200));
  });

  if (!offenders.length) return [];
  return [
    {
      id: "1.4.2",
      description: "Autoplay media >3 s without independent pause/volume control",
      impact: "serious",
      nodes: offenders.map((html) => ({ html, target: [] })),
    },
  ];
};

// -------------------- Tier configuration -----------------------------------
export const tiers = {
  basic: [axeRule], // axe only
  standard: [axeRule, rule_1_4_2_audio], // + a few bespoke heuristics
  premium: [axeRule, rule_1_4_2_audio /* add more bespoke functions here */],
} as const;

export type TierName = keyof typeof tiers; 
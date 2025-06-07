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

export const rule_1_1_1_images: RuleFunction = async (page) => {
  const offenders = await page.evaluate(() => {
    return Array.from(document.querySelectorAll("img"))
      .filter((img) => {
        // Skip images that are clearly decorative
        if (img.getAttribute("role") === "presentation" || 
            img.getAttribute("role") === "none") {
          return false;
        }

        // Skip images with empty alt="" (explicitly marked as decorative)
        if (img.hasAttribute("alt") && img.getAttribute("alt") === "") {
          return false;
        }

        // Skip images that are likely decorative based on context
        const isDecorative = (
          // Images in decorative containers
          img.closest('[role="presentation"], [role="none"]') ||
          // Images with decorative class names
          /\b(decoration|decorative|ornament|divider|spacer|bullet)\b/i.test(img.className) ||
          // Very small images (likely icons or spacers)
          (img.width > 0 && img.height > 0 && img.width <= 10 && img.height <= 10) ||
          // Images with decorative file names
          /\b(decoration|ornament|divider|spacer|bullet|arrow|icon-small)\b/i.test(img.src)
        );

        if (isDecorative) return false;

        // Check if image is informational but missing proper alt
        const hasValidAlt = img.hasAttribute("alt") && 
                           (img.getAttribute("alt")?.trim().length ?? 0) > 0;

        // Image is likely informational if:
        const isInformational = (
          // Inside content areas
          img.closest('article, main, section, .content, .post, .article') ||
          // Has meaningful file names
          /\b(chart|graph|diagram|photo|screenshot|figure|img|image)\b/i.test(img.src) ||
          // Is part of a figure
          img.closest('figure') ||
          // Has a title attribute (suggests meaningful content)
          img.hasAttribute('title') ||
          // Is linked (suggests it's clickable content)
          img.closest('a') ||
          // Default assumption for images without clear decorative markers
          true
        );

        return isInformational && !hasValidAlt;
      })
      .map((img) => ({
        html: img.outerHTML.slice(0, 200),
        src: img.src,
        hasAlt: img.hasAttribute("alt"),
        altText: img.getAttribute("alt") || "",
      }));
  });

  if (!offenders.length) return [];
  
  return [
    {
      id: "1.1.1",
      description: "Informational images missing meaningful alt text",
      impact: "serious",
      nodes: offenders.map((data) => ({
        html: data.html,
        target: [],
        failureMessage: data.hasAlt 
          ? `Image has empty alt attribute: "${data.altText}"`
          : "Image missing alt attribute",
      })),
    },
  ];
};


export const rule_2_5_8_targetSizeMin: RuleFunction = async (page) => {
  const result = await page.evaluate(() => {
    const MIN_SIZE = 24;
    const interactive = Array.from(document.querySelectorAll(`
      a[href], button, input[type=submit], input[type=button],
      [role="button"], [onclick]
    `));

    const violations: any[] = [];

    for (const el of interactive) {
      const rect = el.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      const style = window.getComputedStyle(el);
      const isInline = style.display === 'inline';

      const visible =
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      rect.width > 0 &&
      rect.height > 0;

      const isVisuallyHiddenFocusable = (el as HTMLElement).className.includes("visually-hidden") && (el as HTMLElement).tabIndex >= 0;

      if ((width < MIN_SIZE || height < MIN_SIZE) && 
      !isInline && visible && !isVisuallyHiddenFocusable) {
        violations.push({
          html: el.outerHTML.slice(0, 300),
          target: [el.tagName.toLowerCase() + (el.id ? `#${el.id}` : '')],
          failureSummary: `Pointer target is only ${Math.round(width)}x${Math.round(height)}px. Must be at least 24x24px.`,
        });
      }
    }

    return violations;
  });

  return result.map((v: any) => ({
    id: "2.5.8",
    description: "Target Size (Minimum)",
    impact: "moderate",
    nodes: [v],
  }));
};


// -------------------- Tier configuration -----------------------------------
export const tiers = {
  basic: [axeRule, rule_1_1_1_images], // axe only
  premium: [axeRule, 
    rule_1_4_2_audio, 
    rule_2_5_8_targetSizeMin,
    rule_1_1_1_images /* add more bespoke functions here */],
} as const;

export type TierName = keyof typeof tiers; 
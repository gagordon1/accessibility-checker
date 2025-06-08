from __future__ import annotations

"""wcag_scanner.py – WCAG 2.2 audit (old SDK fallback)"""

import argparse, json, os
from pathlib import Path
from typing import List

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from constants import WCAG_RULES_VECTOR_STORE_ID
from utils.scrape import extract_elements, scroll_to_bottom
from openai_wcag_checker import OpenAIWCAGClient
from type_hints.wcag_types import Violation

load_dotenv()
DEFAULT_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")



def scan_url(url: str, model: str = DEFAULT_MODEL) -> List[Violation]:
    # ── Playwright capture ──────────────────────────────────────────────────
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        page.goto(url, wait_until="networkidle")
        scroll_to_bottom(page)  # Scroll through page to trigger lazy loading
        elements = extract_elements(page)
        img_path = Path("model_context/screenshot.png")
        page.screenshot(path=str(img_path), full_page=True)
        browser.close()

    client = OpenAIWCAGClient()
    text = client.run_check(img_path, WCAG_RULES_VECTOR_STORE_ID, elements)
    print(text)

    return []
    # return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="WCAG scan via older SDK pattern")
    ap.add_argument("url"); ap.add_argument("--model", default=DEFAULT_MODEL)
    res = scan_url(**vars(ap.parse_args()))
    print(json.dumps([v.__dict__ for v in res], indent=2))

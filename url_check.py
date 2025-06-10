from __future__ import annotations

"""wcag_scanner.py – WCAG 2.2 audit (old SDK fallback)"""

import argparse, json, os
from pathlib import Path
from typing import List
from datetime import datetime
import re
import logging

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from constants import WCAG_RULES_VECTOR_STORE_ID
from utils.scrape import extract_elements, scroll_to_bottom, normalize_url
from wcag_client import WCAGAIClient
from type_hints.wcag_types import Violation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()
DEFAULT_MODEL = "deepseek-chat"

def sanitize_url(url: str) -> str:
    """Convert URL to a valid filename."""
    clean_url = re.sub(r'^https?://(www\.)?', '', url)
    clean_url = re.sub(r'[^\w\-\.]', '_', clean_url)
    return clean_url

def save_violations(url: str, violations: List[Violation]) -> str:
    """Save violations to a single JSON file with URLs as keys."""
    violations_file = Path("violations/violations.json")
    violations_file.parent.mkdir(exist_ok=True)
    
    # Load existing data if file exists
    if violations_file.exists():
        with open(violations_file, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    # Update data for this URL
    data[normalize_url(url)] = {
        'timestamp': datetime.now().isoformat(),
        'violations': [v.model_dump() for v in violations]
    }
    
    # Save updated data
    with open(violations_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return str(violations_file)

def scan_url(url: str, model: str = DEFAULT_MODEL) -> List[Violation]:
    # ── Playwright capture ──────────────────────────────────────────────────
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=0.8)
        page.goto(url, wait_until="networkidle")
        scroll_to_bottom(page)  # Scroll through page to trigger lazy loading
        elements = extract_elements(page)
        img_path = Path("model_context/screenshot.png")
        page.screenshot(path=str(img_path), full_page=True)
        logger.info(f"Screenshot of {url} saved to {img_path}")
        browser.close()



    client = WCAGAIClient(model=model)
    logger.info(f"Running WCAG check on {url} with {model} (provider: {client.provider})")
    violations = client.run_check(img_path, WCAG_RULES_VECTOR_STORE_ID, elements)

    # Save violations to file
    filepath = save_violations(url, violations)
    logger.info(f"Violations saved to: {filepath}")

    return violations

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="WCAG scan via older SDK pattern")
    ap.add_argument("url")
    ap.add_argument(
        "--model", 
        default=DEFAULT_MODEL,
        help=f"Model to use for WCAG checking. Available: {', '.join(WCAGAIClient.get_available_models())}"
    )
    res = scan_url(**vars(ap.parse_args()))
    logger.info("Scan results:")
    logger.info(json.dumps([v.model_dump_json() for v in res], indent=2))
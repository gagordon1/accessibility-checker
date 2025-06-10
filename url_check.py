from __future__ import annotations

"""wcag_scanner.py – WCAG 2.2 audit (old SDK fallback)"""

import argparse, json, os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import re
import logging

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from constants import WCAG_RULES_VECTOR_STORE_ID
from utils.scrape import extract_elements, normalize_url, capture_website_with_playwright
from wcag_client import WCAGAIClient
from type_hints.wcag_types import Violation
from axe_scan import run_axe_scan
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

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

def scan_url(url: str, model: Optional[str] = None) -> List[Violation]:
    # ── Playwright capture ──────────────────────────────────────────────────
 

    axe_violations = run_axe_scan(url)

    # Only run AI model if specified
    if model:
        elements, img_path, html_content = capture_website_with_playwright(url, take_screenshot=True)

        if img_path is None:
            raise ValueError("Screenshot was not captured successfully")

        logger.info(f"Running WCAG AI check on {url} with {model}")
        client = WCAGAIClient(model=model)
        logger.info(f"Using provider: {client.provider}")
        ai_violations = client.run_check(img_path, WCAG_RULES_VECTOR_STORE_ID, elements)
        logger.info(f"AI model found {len(ai_violations)} violations")
        all_violations = ai_violations
    else:
        logger.info("No AI model specified, skipping AI-based WCAG check")
        all_violations = []

    # Save violations to file
    filepath = save_violations(url, all_violations + axe_violations)
    logger.info(f"Violations saved to: {filepath}")

    return all_violations + axe_violations

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="WCAG scan via older SDK pattern")
    ap.add_argument("url")
    ap.add_argument(
        "--model", 
        help=f"Model to use for AI-based WCAG checking. Available: {', '.join(WCAGAIClient.get_available_models())}. If not specified, only axe-core will be used."
    )
    res = scan_url(**vars(ap.parse_args()))
    logger.info("Scan results:")
    logger.info(json.dumps([v.model_dump_json() for v in res], indent=2))
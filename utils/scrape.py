from typing import Any, Dict, List, cast, Optional, Tuple
from playwright.sync_api import Page, sync_playwright
from constants import INTERESTING
from urllib.parse import urlparse, urlunparse
import urllib.parse
import logging
import json
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

def normalize_url(url: str) -> str:
    """Normalize URL for consistent caching by removing variations."""
    try:
        # Parse the URL
        parsed = urlparse(url.lower().strip())
        
        # Normalize scheme to https
        scheme = 'https'
        
        # Remove www. prefix
        netloc = parsed.netloc
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        
        # Remove trailing slash from path
        path = parsed.path.rstrip('/')
        if not path:
            path = '/'
        
        # Sort query parameters for consistent ordering
        query = parsed.query
        if query:
            # Parse query parameters and sort them
            params = urllib.parse.parse_qsl(query)
            params.sort()
            query = urllib.parse.urlencode(params)
        
        # Reconstruct normalized URL
        normalized = urlunparse((scheme, netloc, path, parsed.params, query, ''))
        
        logger.debug(f"Normalized URL: {url} -> {normalized}")
        return normalized
        
    except Exception as e:
        logger.warning(f"Failed to normalize URL {url}: {e}")
        return url

def extract_elements(page: Page) -> List[Dict[str, Any]]:
    
    script = """
      function(selector) {
        return Array.from(document.querySelectorAll(selector)).map(function(el) {
          const r = el.getBoundingClientRect();
          const cls = (el.getAttribute('class')||'').trim().split(/\\s+/).map(c=>'.'+c).join('');
          const selectorStr = el.id ? '#'+el.id : el.tagName.toLowerCase()+cls;
          return {
            selector: selectorStr, 
            html: el.outerHTML.slice(0,300), 
            bbox: [r.x, r.y, r.width, r.height]
          };
        });
      }
    """
    return cast(List[Dict[str, Any]], page.evaluate(script, INTERESTING))

def resize_viewport_to_full_page(page):
    """
    Resize the viewport to the full page dimensions to capture everything at once
    This keeps dynamic elements like navbars in correct positions
    """
    # Get the full content dimensions
    dimensions = page.evaluate("""
        () => {
            return {
                width: Math.max(
                    document.body.scrollWidth,
                    document.body.offsetWidth,
                    document.documentElement.clientWidth,
                    document.documentElement.scrollWidth,
                    document.documentElement.offsetWidth
                ),
                height: Math.max(
                    document.body.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.clientHeight,
                    document.documentElement.scrollHeight,
                    document.documentElement.offsetHeight
                )
            };
        }
    """)
    
    # Set viewport to capture full page content
    page.set_viewport_size({
        'width': max(1200, dimensions['width']),  # At least 1200px wide
        'height': min(dimensions['height'], 32767)  # Browser height limit
    })
    
    logger.debug(f"Resized viewport to full page: {max(1200, dimensions['width'])}x{min(dimensions['height'], 32767)}")

def capture_website_with_playwright(url: str, take_screenshot: bool = False, 
                                  screenshot_path: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[Path], str]:
    """
    Capture website content using Playwright with consistent methodology
    
    Args:
        url: The URL to capture
        take_screenshot: Whether to take a screenshot
        screenshot_path: Path to save screenshot (defaults to model_context/screenshot.png)
        
    Returns:
        Tuple of (elements, img_path, png_base64_data)
        - elements: List of extracted elements for AI analysis
        - img_path: Path to screenshot (None if not taken)
        - png_base64_data: Base64 encoded PNG screenshot for embedding in HTML
    """
    logger.info(f"Capturing website content from: {url}")
    
    img_path = None
    if take_screenshot and not screenshot_path:
        screenshot_path = "model_context/screenshot.png"
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        page.goto(url, wait_until="networkidle")
        
        # Resize viewport to full page dimensions to capture everything at once
        resize_viewport_to_full_page(page)
        
        # Extract elements for AI analysis
        elements = extract_elements(page)
        
        # Take screenshot if requested
        if take_screenshot and screenshot_path:
            img_path = Path(screenshot_path)
            img_path.parent.mkdir(exist_ok=True)
            page.screenshot(path=str(img_path), full_page=True)
            logger.info(f"Screenshot of {url} saved to {img_path}")
        
        # Capture PNG screenshot for embedding
        png_screenshot = page.screenshot(full_page=True, type='png')
        png_base64 = base64.b64encode(png_screenshot).decode('utf-8')
        
        browser.close()
    
    logger.info(f"Website capture complete - Elements: {len(elements)}, PNG: {len(png_base64)} chars")
    return elements, img_path, png_base64

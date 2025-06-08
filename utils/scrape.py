from typing import Any, Dict, List, cast
from playwright.sync_api import Page
from constants import INTERESTING
from urllib.parse import urlparse, urlunparse
import urllib.parse
import logging

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
    
    script = f"""
      () => Array.from(document.querySelectorAll('{INTERESTING}')).map(el => {{
        const r = el.getBoundingClientRect();
        const cls = (el.getAttribute('class')||'').trim().split(/\\s+/).map(c=>'.'+c).join('');
        const selector = el.id ? '#'+el.id : el.tagName.toLowerCase()+cls;
        return {{selector, html: el.outerHTML.slice(0,300), bbox:[r.x,r.y,r.width,r.height]}};
      }})
    """
    return cast(List[Dict[str, Any]], page.evaluate(script))


def scroll_to_bottom(page):
    page.evaluate(
        """
        async () => {
            let totalHeight = 0;
            const distance = 500;
            while (totalHeight < document.body.scrollHeight) {
                window.scrollBy(0, distance);
                totalHeight += distance;
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
        """
    )

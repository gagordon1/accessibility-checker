
from typing import Any, Dict, List, cast
from playwright.sync_api import Page
from constants import INTERESTING

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
                await new Promise(resolve => setTimeout(resolve, 300));
            }
            window.scrollTo(0, 0);  // scroll back up if needed
        }
        """
    )

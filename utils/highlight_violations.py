"""
Reusable violation highlighting utilities
Based on the proven logic from the browser extension
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def get_violation_highlight_css() -> str:
    """
    Get the CSS styles for violation highlighting
    Identical to the extension styles for consistency
    
    Returns:
        CSS string for violation highlighting
    """
    return """
        .wcag-violation-icon {
            position: absolute !important;
            width: 28px !important;
            height: 28px !important;
            background-color: #dc3545 !important;
            border: 3px solid white !important;
            border-radius: 50% !important;
            z-index: 999999 !important;
            font-size: 16px !important;
            color: white !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-weight: bold !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.6) !important;
            font-family: Arial, sans-serif !important;
            line-height: 1 !important;
            text-align: center !important;
            top: -14px !important;
            left: -14px !important;
            pointer-events: none !important;
        }
        
        .wcag-highlighted-element {
            position: relative !important;
            outline: 4px solid #dc3545 !important;
            outline-offset: 2px !important;
        }
    """

def get_violation_highlight_javascript(violations: List[Dict]) -> str:
    """
    Get the JavaScript code for highlighting violations
    Uses the exact same logic as the proven extension
    
    Args:
        violations: List of violation dictionaries with target selectors
        
    Returns:
        JavaScript function string for highlighting
    """
    return """
        (violations) => {
            let successful_annotations = 0;
            let failed_annotations = [];
            let violationNumber = 0;
            
            violations.forEach((violation, violationIndex) => {
                violation.nodes.forEach((node, nodeIndex) => {
                    (node.target || []).forEach((selector) => {
                        try {
                            const elements = document.querySelectorAll(selector);
                            
                            elements.forEach((el, elementIndex) => {
                                // Only add once
                                if (!el.dataset.wcagFlagged) {
                                    violationNumber++;
                                    
                                    // Highlight the element (exact same as extension)
                                    el.style.outline = "3px solid red";
                                    el.classList.add('wcag-highlighted-element');
                                    el.dataset.wcagFlagged = "true";
                                    
                                    // Create numbered icon (similar to extension but simplified for screenshots)
                                    const icon = document.createElement('div');
                                    icon.className = 'wcag-violation-icon';
                                    icon.textContent = violationNumber;
                                    icon.dataset.wcagIcon = 'true';
                                    
                                    // Ensure element can contain the icon
                                    if (window.getComputedStyle(el).position === 'static') {
                                        el.style.position = 'relative';
                                    }
                                    
                                    // Add icon to element
                                    el.appendChild(icon);
                                    
                                    successful_annotations++;
                                }
                            });
                        } catch (e) {
                            // Invalid selectors shouldn't crash the highlighting
                            failed_annotations.push({
                                selector: selector,
                                error: e.message
                            });
                        }
                    });
                });
            });
            
            return {
                successful_annotations: successful_annotations,
                failed_annotations: failed_annotations,
                total_violations: violationNumber
            };
        }
    """

def highlight_violations_on_page(page, violations: List[Dict]) -> Dict:
    """
    Apply violation highlighting to a Playwright page
    
    Args:
        page: Playwright page object
        violations: List of violation dictionaries
        
    Returns:
        Dictionary with highlighting results
    """
    if not violations:
        logger.info("No violations to highlight")
        return {
            'successful_annotations': 0,
            'failed_annotations': [],
            'total_violations': 0
        }
    
    # Inject CSS styles
    page.add_style_tag(content=get_violation_highlight_css())
    
    # Execute highlighting JavaScript
    result = page.evaluate(get_violation_highlight_javascript(violations), violations)
    
    # Log results
    successful = result.get('successful_annotations', 0)
    failed = result.get('failed_annotations', [])
    total = result.get('total_violations', 0)
    
    if failed:
        logger.warning(f"Failed to annotate {len(failed)} selectors:")
        for failure in failed:
            logger.warning(f"  {failure['selector']}: {failure['error']}")
    
    logger.info(f"Highlighted {successful}/{total} violations successfully")
    return result

def clear_violations_javascript() -> str:
    """
    Get JavaScript to clear existing violation highlights
    
    Returns:
        JavaScript function string for clearing highlights
    """
    return """
        () => {
            // Remove all violation icons
            const icons = document.querySelectorAll('.wcag-violation-icon');
            icons.forEach(icon => icon.remove());
            
            // Remove highlighting from elements
            const highlightedElements = document.querySelectorAll('.wcag-highlighted-element');
            highlightedElements.forEach(el => {
                el.style.outline = '';
                el.classList.remove('wcag-highlighted-element');
                delete el.dataset.wcagFlagged;
            });
            
            return { cleared: icons.length + highlightedElements.length };
        }
    """

def clear_violations_on_page(page) -> Dict:
    """
    Clear existing violation highlights from a Playwright page
    
    Args:
        page: Playwright page object
        
    Returns:
        Dictionary with clearing results
    """
    result = page.evaluate(clear_violations_javascript())
    cleared = result.get('cleared', 0)
    logger.info(f"Cleared {cleared} existing violation highlights")
    return result 
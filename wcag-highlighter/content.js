/**
 * 1. Ask background.js to fetch violations for this page.
 * 2. When they come back, highlight each node.target selector.
 */

// Add CSS styles for the icons
const iconStyles = `
  .wcag-violation-icon {
    position: fixed !important;
    width: 20px !important;
    height: 20px !important;
    background-color: #dc3545 !important;
    border: 2px solid white !important;
    border-radius: 50% !important;
    cursor: pointer !important;
    z-index: 999999 !important;
    font-size: 12px !important;
    color: white !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-weight: bold !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.5) !important;
    font-family: Arial, sans-serif !important;
    line-height: 1 !important;
    text-align: center !important;
  }
  
  .wcag-violation-tooltip {
    position: fixed !important;
    background: #333 !important;
    color: white !important;
    padding: 8px 12px !important;
    border-radius: 4px !important;
    font-size: 12px !important;
    max-width: 300px !important;
    z-index: 1000000 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5) !important;
    pointer-events: none !important;
    opacity: 0 !important;
    transition: opacity 0.2s !important;
    line-height: 1.4 !important;
    font-family: Arial, sans-serif !important;
  }
  
  .wcag-violation-tooltip.show {
    opacity: 1 !important;
  }
  
  .wcag-highlighted-element {
    position: relative !important;
  }
`;

// Inject styles into the page
const styleSheet = document.createElement('style');
styleSheet.textContent = iconStyles;
document.head.appendChild(styleSheet);

// --- 1. Kick off the fetch with error handling ---
function requestViolations() {
  chrome.runtime.sendMessage({
    action: "fetch_violations",
    url: window.location.href
  }, (response) => {
    if (chrome.runtime.lastError) {
      console.warn("WCAG extension: Failed to send message:", chrome.runtime.lastError.message);
      // Retry after a short delay
      setTimeout(requestViolations, 1000);
    }
  });
}

// Wait a bit for the page and extension to be fully loaded
setTimeout(requestViolations, 500);

// --- 2. Receive results and highlight ---
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "deliver_error") {
    console.warn("WCAG extension:", msg.error);
    return;
  }

  if (msg.action === "deliver_violations") {
    highlightViolations(msg.violations);
  }
});

/**
 * Outline every selector that appears in the violations list.
 * Each violation has .description and .nodes[].target[] (CSS selectors).
 */
function highlightViolations(violations) {
  console.log("Highlighting violations:", violations); // Debug log
  
  violations.forEach((violation, violationIndex) => {
    violation.nodes.forEach((node, nodeIndex) => {
      (node.target || []).forEach((selector) => {
        try {
          const elements = document.querySelectorAll(selector);
          console.log(`Found ${elements.length} elements for selector:`, selector); // Debug log
          
          elements.forEach((el, elementIndex) => {
            // Only add once
            if (!el.dataset.wcagFlagged) {
              // Highlight the element
              el.style.outline = "3px solid red";
              el.classList.add('wcag-highlighted-element');
              el.dataset.wcagFlagged = "true";
              
              // Create and add the icon
              const icon = createViolationIcon(violation, node, violationIndex, nodeIndex, elementIndex, el);
              document.body.appendChild(icon); // Append to body instead of element
              
              console.log("Added icon for element:", el); // Debug log
            }
          });
        } catch (e) {
          // Invalid selectors shouldn't crash the extension
          console.debug("WCAG extension – bad selector:", selector, e);
        }
      });
    });
  });

  console.info(`WCAG extension: highlighted ${violations.length} violations`);
}

/**
 * Create a violation icon with hover tooltip
 */
function createViolationIcon(violation, node, violationIndex, nodeIndex, elementIndex, targetElement) {
  const icon = document.createElement('div');
  icon.className = 'wcag-violation-icon';
  icon.textContent = '!';
  icon.dataset.wcagIcon = 'true';
  
  // Position the icon relative to the target element
  function positionIcon() {
    const rect = targetElement.getBoundingClientRect();
    
    icon.style.position = 'fixed';
    icon.style.left = (rect.right - 8) + 'px';
    icon.style.top = (rect.top - 8) + 'px';
  }
  
  // Initial positioning
  positionIcon();
  
  // Update position on scroll and resize
  const updatePosition = () => positionIcon();
  window.addEventListener('scroll', updatePosition);
  window.addEventListener('resize', updatePosition);
  
  // Create tooltip
  const tooltip = document.createElement('div');
  tooltip.className = 'wcag-violation-tooltip';
  
  // Build tooltip content
  let tooltipContent = `<strong>WCAG Violation</strong><br><br>`;
  tooltipContent += `<strong>Issue:</strong> ${violation.description || 'No description available'}<br><br>`;
  
  if (violation.impact) {
    tooltipContent += `<strong>Impact:</strong> ${violation.impact}<br><br>`;
  }
  
  if (node.failureSummary) {
    tooltipContent += `<strong>Details:</strong> ${node.failureSummary}<br><br>`;
  }
  
  if (violation.id) {
    tooltipContent += `<strong>Rule ID:</strong> ${violation.id}`;
  }
  
  tooltip.innerHTML = tooltipContent;
  document.body.appendChild(tooltip);
  
  // Add hover events
  icon.addEventListener('mouseenter', (e) => {
    const rect = icon.getBoundingClientRect();
    tooltip.style.left = Math.min(rect.left, window.innerWidth - 320) + 'px';
    tooltip.style.top = (rect.bottom + 5) + 'px';
    tooltip.classList.add('show');
  });
  
  icon.addEventListener('mouseleave', () => {
    tooltip.classList.remove('show');
  });
  
  // Clean up when target element or icon is removed
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.removedNodes.forEach((node) => {
        if (node === icon || node === targetElement || node.contains && (node.contains(icon) || node.contains(targetElement))) {
          window.removeEventListener('scroll', updatePosition);
          window.removeEventListener('resize', updatePosition);
          if (tooltip.parentNode) tooltip.remove();
          if (icon.parentNode) icon.remove();
          observer.disconnect();
        }
      });
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
  
  return icon;
}

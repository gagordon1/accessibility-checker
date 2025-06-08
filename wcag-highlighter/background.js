/**
 * Background worker: listens for a request from the content script,
 * fetches violations from Flask, then sends them back.
 */

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  // ---------- from popup ----------
  if (msg.action === "popup_scan") {
    const api = `http://localhost:5000/api/violations?url=${encodeURIComponent(
      msg.url
    )}`;

    fetch(api)
      .then(res => res.json())
      .then(data => {
        if (data.violations) {
          chrome.tabs.sendMessage(msg.tabId, {
            action: "deliver_violations",
            violations: data.violations
          });
          
          // reply to popup
          sendResponse({ ok: true, count: data.violations.length });
        } else {
          sendResponse({ ok: false, error: data.error || "No violations" });
        }
      })
      .catch(err => {
        sendResponse({ ok: false, error: err.message });
      });
    
    // Keep the message channel open for the async fetch
    return true;
  }
  
  // ---------- from content script ----------
  if (msg.action === "fetch_violations") {
    const api = `http://localhost:5000/api/violations?url=${encodeURIComponent(msg.url)}`;

    fetch(api)
      .then(res => res.json())
      .then(json => {
        if (json.violations) {
          chrome.tabs.sendMessage(sender.tab.id, {
            action: "deliver_violations",
            violations: json.violations
          });
        } else {
          chrome.tabs.sendMessage(sender.tab.id, {
            action: "deliver_error",
            error: json.error || "No violations array in response."
          });
        }
        sendResponse({ success: true });
      })
      .catch(err => {
        chrome.tabs.sendMessage(sender.tab.id, {
          action: "deliver_error",
          error: err.message
        });
        sendResponse({ success: false, error: err.message });
      });
    
    // Keep the message channel open for the async fetch
    return true;
  }
});

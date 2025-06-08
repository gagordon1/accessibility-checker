const btn    = document.getElementById("scanBtn");
const status = document.getElementById("status");

btn.addEventListener("click", async () => {
  status.textContent = "Scanning…";

  // Get the active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return (status.textContent = "No active tab.");

  // Ask background.js to fetch violations for this tab
  chrome.runtime.sendMessage(
    { action: "popup_scan", url: tab.url, tabId: tab.id },
    (resp) => {
      if (chrome.runtime.lastError) {
        status.textContent = chrome.runtime.lastError.message;
        return;
      }
      if (resp && resp.ok) {
        status.textContent = `Highlighted ${resp.count} violations`;
      } else {
        status.textContent = resp?.error || "Unknown error";
      }
    }
  );
});

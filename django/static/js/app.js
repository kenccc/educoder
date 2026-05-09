// Wire CSRF for HTMX requests so POSTs from hx-post work out of the box.
document.body.addEventListener("htmx:configRequest", (event) => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  if (token) {
    event.detail.headers["X-CSRFToken"] = token;
  }
});

// Optional: open a websocket on submission detail pages for live updates.
function openSubmissionSocket(submissionId, onMessage) {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/submission/${submissionId}/`);
  ws.addEventListener("message", (e) => onMessage(JSON.parse(e.data)));
  return ws;
}
window.openSubmissionSocket = openSubmissionSocket;

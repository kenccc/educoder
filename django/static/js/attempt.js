/* attempt.js — runs ONLY on /assignments/attempt/<id>/.
 *
 * Responsibilities:
 *   1. Fullscreen lock (strict mode).
 *   2. Block paste/copy/cut/contextmenu and devtools shortcuts.
 *   3. Detect devtools opening (window-size delta + debugger trick).
 *   4. MutationObserver on protected nodes — flag DOM tampering.
 *   5. Visibility / blur / fullscreen-exit detection.
 *   6. Live timer; freeze the IDE on expiry.
 *   7. Submit pipeline (Python via HTMX + WebSocket polling, Web via iframe).
 *   8. Send every event over WebSocket — server is authoritative.
 */
(() => {
  const script = document.currentScript || document.querySelector('script[src*="attempt.js"]');
  const ATTEMPT_ID = script.dataset.attemptId;
  const STRICT     = script.dataset.strict === '1';
  const LANGUAGE   = script.dataset.language;
  let   remaining  = parseInt(script.dataset.timeLimit || '', 10);
  if (isNaN(remaining)) remaining = null;

  const $ = (sel) => document.querySelector(sel);
  const cheatCount = $('#cheatCount');
  const veil       = $('#cheatVeil');
  const veilLog    = $('#cheatVeilLog');
  const reBtn      = $('#reenterFsBtn');
  const runBtn     = $('#runBtn');
  const status     = $('#status');
  const results    = $('#results');
  const summary    = $('#resultsSummary');
  const timerEl    = $('#timer');
  const codeField  = $('#codeField');
  const submitForm = $('#submitForm');

  let cheatTotal = parseInt(cheatCount?.textContent || '0', 10) || 0;
  let frozen     = false;
  let socket;

  // ---------------- WebSocket ----------------
  function connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    socket = new WebSocket(`${proto}://${location.host}/ws/attempt/${ATTEMPT_ID}/`);
    socket.addEventListener('close', () => {
      // reconnect with light backoff
      setTimeout(connect, 1500);
    });
  }
  connect();

  function emit(kind, payload = {}, severity = 1) {
    if (frozen) return;
    cheatTotal++;
    if (cheatCount) cheatCount.textContent = String(cheatTotal);
    const msg = { kind, severity, ...payload, at: Date.now() };
    try { socket && socket.readyState === 1 && socket.send(JSON.stringify(msg)); } catch {}
    if (veilLog) {
      const line = document.createElement('div');
      line.textContent = `· ${kind} · ${new Date().toLocaleTimeString()}`;
      veilLog.prepend(line);
      while (veilLog.children.length > 6) veilLog.lastChild.remove();
    }
  }
  window.__emitCheat = emit;

  // ---------------- Fullscreen lock ----------------
  function inFullscreen() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement);
  }
  async function enterFullscreen() {
    try {
      const el = document.documentElement;
      if (el.requestFullscreen)        await el.requestFullscreen();
      else if (el.webkitRequestFullscreen) await el.webkitRequestFullscreen();
    } catch (e) { /* user may dismiss */ }
  }
  function showVeil() { veil?.classList.remove('hidden'); }
  function hideVeil() { veil?.classList.add('hidden'); }

  if (STRICT) {
    // Initial fullscreen — must be triggered by a user gesture in some browsers.
    showVeil();
    reBtn?.addEventListener('click', async () => {
      await enterFullscreen();
      if (inFullscreen()) hideVeil();
    });
    document.addEventListener('fullscreenchange', () => {
      if (!inFullscreen() && !frozen) {
        emit('fullscreen', { exited: true }, 2);
        showVeil();
      }
    });
    document.addEventListener('webkitfullscreenchange', () => {
      if (!inFullscreen() && !frozen) showVeil();
    });
  } else {
    hideVeil();
  }

  // ---------------- Clipboard / context-menu blockers ----------------
  const blockEvents = ['copy', 'cut', 'paste', 'contextmenu', 'dragstart', 'drop'];
  blockEvents.forEach((evt) => {
    document.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      emit(evt === 'contextmenu' ? 'contextmenu' : evt, { target: (e.target?.tagName || '').toLowerCase() }, 1);
    }, { capture: true });
  });

  // ---------------- Forbidden key combos ----------------
  document.addEventListener('keydown', (e) => {
    const k = (e.key || '').toLowerCase();
    const forbidden =
      e.key === 'F12' ||
      ((e.ctrlKey || e.metaKey) && e.shiftKey && ['i','j','c'].includes(k)) ||  // devtools
      ((e.ctrlKey || e.metaKey) && k === 'u') ||                                 // view source
      ((e.ctrlKey || e.metaKey) && k === 's') ||                                 // save
      ((e.ctrlKey || e.metaKey) && k === 'p');                                   // print
    if (forbidden) {
      e.preventDefault();
      e.stopPropagation();
      emit('key_combo', { key: k, ctrl: e.ctrlKey, meta: e.metaKey, shift: e.shiftKey }, 2);
      return;
    }
    // Ctrl+C / Ctrl+V on the document body — also blocked by `copy/paste` handlers,
    // but log explicitly here too for keyboard-only attempts.
    if ((e.ctrlKey || e.metaKey) && (k === 'c' || k === 'v' || k === 'x')) {
      // CodeMirror handles these for the editor itself; we just log if they fire here.
      // Actual cancellation is done by clipboard event handler.
    }
  }, { capture: true });

  // ---------------- DevTools detection ----------------
  let devtoolsOpen = false;
  function checkDevtools() {
    const wThreshold = 160;
    const hThreshold = 160;
    const widthDiff  = window.outerWidth - window.innerWidth;
    const heightDiff = window.outerHeight - window.innerHeight;
    const open = widthDiff > wThreshold || heightDiff > hThreshold;
    if (open !== devtoolsOpen) {
      devtoolsOpen = open;
      if (open) emit('devtools', { widthDiff, heightDiff }, 3);
    }
  }
  setInterval(checkDevtools, 1500);

  // Slow-debugger trick: if devtools is "paused" (panel open on debug),
  // the `debugger` statement takes measurable time.
  setInterval(() => {
    const t0 = performance.now();
    try { debugger; } catch {}
    const dt = performance.now() - t0;
    if (dt > 100) emit('devtools', { method: 'debugger', dt }, 3);
  }, 4000);

  // ---------------- Visibility + blur ----------------
  window.addEventListener('blur',  () => emit('tab_blur', {}, 2));
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) emit('visibility', { hidden: true }, 2);
  });

  // Block opening new windows
  const origOpen = window.open;
  window.open = function () { emit('network_open', {}, 3); return null; };

  // ---------------- DOM tampering watcher ----------------
  // Protect critical structural elements; if they vanish or attrs change,
  // flag and re-render from server.
  const targets = [document.body, document.querySelector('header'), document.querySelector('main'), runBtn].filter(Boolean);
  const observer = new MutationObserver((muts) => {
    let suspicious = false;
    for (const m of muts) {
      // Removal of large parts of the page is a red flag.
      if (m.type === 'childList' && (m.removedNodes?.length || 0) > 0) {
        for (const n of m.removedNodes) {
          if (n.nodeType === 1 && (n.id === 'cheatVeil' || n.classList?.contains('anticheat-veil'))) {
            suspicious = true;
          }
        }
      }
    }
    if (suspicious) {
      emit('dom_tamper', {}, 3);
      // Re-insert veil shell if removed
      if (!document.getElementById('cheatVeil')) location.reload();
    }
  });
  targets.forEach((t) => observer.observe(t, { childList: true, subtree: true, attributes: true }));

  // ---------------- Timer ----------------
  function fmt(s) {
    const m = Math.floor(s / 60), r = s % 60;
    return `${String(m).padStart(2,'0')}:${String(r).padStart(2,'0')}`;
  }
  function tick() {
    if (remaining === null || frozen) return;
    if (remaining <= 0) {
      timerEl && (timerEl.textContent = '00:00');
      freeze('time-up');
      return;
    }
    timerEl && (timerEl.textContent = fmt(remaining));
    if (remaining <= 60) timerEl?.classList.add('danger');
    else if (remaining <= 180) timerEl?.classList.add('warning');
    remaining--;
  }
  if (remaining !== null && timerEl) {
    tick();
    setInterval(tick, 1000);
  }
  function freeze(reason) {
    frozen = true;
    if (runBtn) runBtn.disabled = true;
    showVeil();
    if (veil) {
      veil.querySelector('h2').textContent = "Time's up.";
      veil.querySelector('p').textContent  = "Your attempt has ended. Submissions are no longer accepted.";
      reBtn && (reBtn.style.display = 'none');
    }
  }

  // ---------------- Code snapshot capture ----------------
  // 30s debounce: every keystroke resets a timer; if 30s of inactivity passes,
  // the current buffer is shipped server-side. Fires too on run/submit.
  const csrf = () => document.querySelector('meta[name="csrf-token"]').content;
  let snapTimer = null, lastSnapCode = '';
  function postSnapshot(trigger) {
    const code = (window.__getCode && window.__getCode()) || '';
    if (!code || code === lastSnapCode) return;
    lastSnapCode = code;
    fetch(`/assignments/attempt/${ATTEMPT_ID}/snapshot/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      credentials: 'same-origin',
      body: JSON.stringify({ code, trigger }),
    }).catch(() => {});
  }
  function scheduleSnapshot() {
    if (frozen) return;
    if (snapTimer) clearTimeout(snapTimer);
    snapTimer = setTimeout(() => postSnapshot('debounce'), 30000);
  }
  document.addEventListener('keydown', scheduleSnapshot, true);
  document.addEventListener('input', scheduleSnapshot, true);

  // ---------------- Hints ----------------
  const hintsList = document.getElementById('hintsList');
  if (hintsList) {
    // Server gives a URL pattern with hint id 0 — we substitute the real id.
    // Avoids hard-coding the /library/ vs /exercises/ prefix in JS.
    const urlTemplate = hintsList.dataset.revealUrlTemplate || '';
    hintsList.addEventListener('click', async (e) => {
      const btn = e.target.closest('[data-hint-reveal]');
      if (!btn) return;
      const hintId = btn.dataset.hintReveal;
      const url = urlTemplate.replace(/\/0\/reveal\/?$/, `/${hintId}/reveal/`);
      btn.disabled = true;
      try {
        const r = await fetch(url, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
          credentials: 'same-origin',
        });
        if (!r.ok) { btn.disabled = false; return; }
        const data = await r.json();
        const content = hintsList.querySelector(`[data-hint-content="${hintId}"]`);
        if (content) content.style.display = '';
        btn.outerHTML = `<span class="chip chip-pass">revealed</span>`;
      } catch { btn.disabled = false; }
    });
  }

  // ---------------- Run / submit ----------------
  runBtn?.addEventListener('click', async () => {
    if (frozen) return;
    const code = (window.__getCode && window.__getCode()) || '';
    // No client-side run snapshot: server-side `SubmissionService.create_and_dispatch`
    // creates the run-trigger snapshot from the submitted code. Avoids dupe rows.
    if (LANGUAGE === 'web') {
      submitWeb(code);
    } else {
      submitPython(code);
    }
  });

  async function submitPython(code) {
    if (codeField) codeField.value = code;
    summary.textContent = 'running...';
    results.innerHTML = '';
    htmx.trigger(submitForm, 'submit');
  }

  async function submitWeb(code) {
    summary.textContent = 'running...';
    results.innerHTML = '';

    // Create a submission row server-side first, then post results back.
    const formData = new FormData();
    formData.append('code', code);
    const csrf = document.querySelector('meta[name="csrf-token"]').content;
    const r = await fetch(submitForm.action, {
      method: 'POST',
      body: formData,
      headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest' },
      redirect: 'manual',
      credentials: 'same-origin',
    });
    if (r.type === 'opaqueredirect' || r.status === 401 || r.status === 403) {
      summary.textContent = 'session expired — reload';
      return;
    }
    if (!r.ok) {
      const txt = await r.text();
      summary.textContent = `error ${r.status}`;
      results.textContent = txt.slice(0, 500);
      return;
    }
    const html = await r.text();
    status.innerHTML = html;

    const subId = status.querySelector('[data-submission-id]')?.dataset.submissionId;
    if (!subId) {
      summary.textContent = 'submission failed';
      return;
    }

    const cases = window.__webCases || [];
    const iframe = document.getElementById('webRunner');
    const runResults = await runCasesInIframe(iframe, code, cases);
    runResults.forEach(renderResult);

    const rr = await fetch(`/submissions/${subId}/web-results/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify({ results: runResults }),
    });
    if (rr.ok) {
      status.innerHTML = await rr.text();
    }
    const passed = runResults.filter(r => r.passed).length;
    summary.textContent = `${passed}/${runResults.length} passed`;
  }

  function renderResult(r) {
    const div = document.createElement('div');
    div.className = 'card !p-3 flex items-center justify-between text-sm';
    div.innerHTML = `<span class="text-warm-parchment">${r.name}${r.is_hidden ? ' <span class="caps text-stone">hidden</span>' : ''}</span>
                     <span class="chip ${r.passed ? 'chip-pass' : 'chip-fail'}">${r.passed ? 'pass' : 'fail'}</span>`;
    results.appendChild(div);
  }

  // Iframe is sandboxed without allow-same-origin (student code is untrusted).
  // Parent cannot read iframe DOM directly — we inject a runner script into the
  // srcdoc and exchange messages via postMessage.
  function runCasesInIframe(iframe, userCode, cases) {
    const RUNNER = `<script>(function(){
      function check(c){
        try {
          for (var i=0;i<(c.assertions||[]).length;i++){
            var a=c.assertions[i], el;
            if (a.kind==='selector'){
              if (!document.querySelector(a.selector)) return {ok:false,err:'missing '+a.selector};
            } else if (a.kind==='text'){
              el=document.querySelector(a.selector);
              if (!el||el.textContent.indexOf(a.text)===-1) return {ok:false,err:a.selector+' should contain "'+a.text+'"'};
            } else if (a.kind==='attr'){
              el=document.querySelector(a.selector);
              if (!el||el.getAttribute(a.attr)!==a.value) return {ok:false,err:a.selector+'['+a.attr+'] != "'+a.value+'"'};
            } else if (a.kind==='count'){
              var els=document.querySelectorAll(a.selector);
              if (els.length!==a.count) return {ok:false,err:'expected '+a.count+' of '+a.selector+', got '+els.length};
            } else if (a.kind==='js'){
              var fn=new Function('window','document','try { return Boolean('+a.expr+'); } catch(e){ return false; }');
              if (!fn(window,document)) return {ok:false,err:'expr failed: '+a.expr};
            }
          }
          return {ok:true};
        } catch(e){ return {ok:false, err:String(e)}; }
      }
      window.addEventListener('message', function(ev){
        var d=ev.data||{};
        if (d.type!=='run-assertions') return;
        var out=(d.cases||[]).map(function(c){
          var r=check(c);
          return {name:c.name, passed:r.ok, is_hidden:c.is_hidden, error:r.err||null};
        });
        parent.postMessage({type:'assertions-result', nonce:d.nonce, results:out}, '*');
      });
      parent.postMessage({type:'runner-ready'}, '*');
    })();<\/script>`;

    return new Promise((resolve, reject) => {
      const nonce = Math.random().toString(36).slice(2);
      let timer;
      const onMsg = (ev) => {
        if (ev.source !== iframe.contentWindow) return;
        const d = ev.data || {};
        if (d.type === 'runner-ready') {
          iframe.contentWindow.postMessage({ type: 'run-assertions', nonce, cases }, '*');
        } else if (d.type === 'assertions-result' && d.nonce === nonce) {
          window.removeEventListener('message', onMsg);
          clearTimeout(timer);
          resolve(d.results || []);
        }
      };
      window.addEventListener('message', onMsg);
      timer = setTimeout(() => {
        window.removeEventListener('message', onMsg);
        resolve(cases.map(c => ({ name: c.name, passed: false, is_hidden: c.is_hidden, error: 'timeout' })));
      }, 5000);
      iframe.srcdoc = userCode + RUNNER;
    });
  }

  // After every status fragment swap, refresh summary text.
  document.body.addEventListener('htmx:afterSwap', () => {
    const el = status.querySelector('[data-submission-id]');
    if (!el) return;
    const passed = parseInt(el.dataset.passed || '0', 10);
    const total  = parseInt(el.dataset.total  || '0', 10);
    if (total) summary.textContent = `${passed}/${total} passed`;
  });

  // CSRF for HTMX
  document.body.addEventListener('htmx:configRequest', (e) => {
    const t = document.querySelector('meta[name="csrf-token"]')?.content;
    if (t) e.detail.headers['X-CSRFToken'] = t;
  });
})();

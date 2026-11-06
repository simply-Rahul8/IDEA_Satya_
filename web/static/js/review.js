/* Satya review screen (variant B): tracing, tabs, gate, HTMX hooks. Loaded by the review page only. */
(() => {
  'use strict';
  const { $, $$, say, reduced } = window.satya;
  const val = (e) => (typeof e.detail === 'string' ? e.detail : (e.detail.value ?? e.detail));
  const wide = matchMedia('(min-width: 60rem)');
  const rowOf = (el) => el.closest('.row');
  const ta = (sid) => document.getElementById('t-' + sid);
  const smooth = () => (reduced() ? 'auto' : 'smooth');
  const sheetOpen = () => { const d = $('#sheet'); return d && d.open; };
  let selected = '';

  const setTab = (name, focus) => {
    $$('[data-tab]').forEach((b) => {
      const on = b.dataset.tab === name;
      b.setAttribute('aria-selected', String(on));
      b.tabIndex = on ? 0 : -1;
      if (on && focus) b.focus();
    });
    $('#pane-copy').hidden = name !== 'copy';
    $('#pane-truth').hidden = name !== 'truth';
  };

  const peekOf = (c) => document.getElementById('peek-' + rowOf(c).dataset.sid + '-' + c.dataset.anchor);
  const syncAnchors = () => $$('[data-anchor]').forEach((c) => {
    const on = c.dataset.anchor === selected;
    if (wide.matches) {
      c.removeAttribute('aria-expanded'); c.removeAttribute('aria-controls');
      c.setAttribute('aria-pressed', String(on));
    } else {
      c.removeAttribute('aria-pressed');
      c.setAttribute('aria-expanded', String(on));
      c.setAttribute('aria-controls', peekOf(c).id);
    }
    peekOf(c).hidden = wide.matches || !on;
    rowOf(c).classList.toggle('is-linked', wide.matches && on);
  });
  const claimEl = (id) => document.getElementById('claim-' + id);
  const claimName = (c) => c.querySelector('strong').textContent;
  const clearSource = () => { selected = ''; $$('.is-source').forEach((c) => c.classList.remove('is-source')); syncAnchors(); };

  const pick = (id) => {
    const same = selected === id;
    clearSource();
    if (same) return;
    selected = id; syncAnchors();
    const c = claimEl(id);
    if (wide.matches && c) { // desktop: the ledger is beside the copy. Mobile: the inline peek is the trace.
      c.classList.add('is-source');
      c.scrollIntoView({ block: 'nearest', behavior: smooth() });
      say('Source claim highlighted: ' + claimName(c) + '.');
    }
  };
  const openClaim = (id, from) => {
    selected = id; syncAnchors(); setTab('truth');
    $$('.is-source').forEach((c) => c.classList.remove('is-source'));
    const c = claimEl(id);
    c.classList.add('is-source'); c.focus(); c.scrollIntoView({ block: 'nearest', behavior: smooth() });
    const back = $('#back-btn'), r = document.getElementById('s-' + from);
    if (back && r) { back.dataset.back = from; back.textContent = 'Back to ' + document.getElementById('h-' + from).textContent.split(',')[0]; back.hidden = false; }
    say('Source claim highlighted: ' + claimName(c) + '.');
  };
  const goSentence = (sid) => {
    setTab('copy');
    const t = ta(sid), r = t && rowOf(t);
    if (!t) return;
    t.focus(); r.scrollIntoView({ block: 'nearest', behavior: smooth() });
    r.classList.add('is-linked'); setTimeout(() => r.classList.remove('is-linked'), 1200);
    const back = $('#back-btn'); if (back) back.hidden = true;
  };
  const nextIssue = () => { // red first, then amber, then unchecked; wraps
    const rank = { red: 0, amber: 1, unchecked: 2 };
    const open = $$('.row').filter((r) => r.dataset.status in rank).sort((a, b) => rank[a.dataset.status] - rank[b.dataset.status]);
    if (!open.length) return null;
    const cur = document.activeElement && document.activeElement.closest && document.activeElement.closest('.row');
    return open[(open.indexOf(cur) + 1) % open.length];
  };
  const focusRow = (r) => { setTab('copy'); r.querySelector('textarea').focus(); r.scrollIntoView({ block: 'nearest', behavior: smooth() }); };

  document.addEventListener('click', (e) => { // capture: a blocked Approve never posts; it explains and moves focus
    const b = e.target.closest('[data-approve][aria-disabled="true"]');
    if (!b) return;
    e.preventDefault(); e.stopImmediatePropagation();
    const r = nextIssue(); if (r) focusRow(r);
    say($('#note') ? $('#note').textContent : 'Approval is blocked.');
  }, true);
  document.addEventListener('click', (e) => {
    const hit = (s) => e.target.closest(s);
    let m;
    if ((m = hit('[data-anchor]'))) return pick(m.dataset.anchor);
    if ((m = hit('[data-open-claim]'))) return openClaim(m.dataset.openClaim, m.dataset.from);
    if ((m = hit('[data-used-in]'))) return goSentence(m.dataset.usedIn);
    if ((m = hit('#back-btn'))) return goSentence(m.dataset.back);
    if ((m = hit('[data-next]'))) { const r = m.getAttribute('aria-disabled') === 'true' ? null : nextIssue(); if (r) focusRow(r); return; }
    if ((m = hit('[data-tab]'))) return setTab(m.dataset.tab);
    if ((m = hit('[data-recheck]'))) return rowOf(m).querySelector('textarea').dispatchEvent(new Event('satya:recheck'));
    if ((m = hit('[data-skip]'))) {
      e.preventDefault();
      if (m.dataset.skip === 'truth') { setTab('truth'); $('.claim').focus(); } else { setTab('copy'); $('#pane-copy').focus(); }
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && selected && !sheetOpen()) clearSource();
    const tab = e.target.closest && e.target.closest('[data-tab]');
    if (tab && ['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) {
      e.preventDefault();
      const tabs = $$('[data-tab]'), i = tabs.indexOf(tab);
      const to = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      setTab(tabs[to].dataset.tab, true);
    }
  });
  wide.addEventListener('change', syncAnchors);

  /* Gate: condense on scroll; publish heights so sticky offsets are never magic numbers (SC 2.4.11). */
  const gate = $('#gate');
  const measure = () => {
    const root = document.documentElement.style, dock = $('#dock');
    root.setProperty('--gate-h', (getComputedStyle(gate).position === 'sticky' ? gate.offsetHeight : 0) + 'px');
    root.setProperty('--dock-h', (dock && dock.offsetParent !== null ? dock.offsetHeight : 0) + 'px');
  };
  if (gate) {
    new ResizeObserver(measure).observe(gate);
    addEventListener('resize', measure);
    addEventListener('scroll', () => { gate.dataset.condensed = String(scrollY > 120); }, { passive: true });
    measure();
  }
  addEventListener('offline', () => { $('#offline-notice').hidden = false; });
  addEventListener('online', () => { $('#offline-notice').hidden = true; });

  /* HTMX: the sentence textarea is never swapped; drop stale responses; keep the row edge in sync. */
  const isSentence = (el) => el && el.tagName === 'TEXTAREA' && el.dataset.sid;
  document.addEventListener('input', (e) => {
    if (!isSentence(e.target)) return;
    const b = document.getElementById('backdrop-' + e.target.id);
    if (b) b.textContent = e.target.value + (e.target.value.endsWith('\n') ? ' ' : '');
  });
  document.addEventListener('htmx:beforeRequest', (e) => {
    if (isSentence(e.target)) { e.detail.xhr.satyaSent = e.target.value; rowOf(e.target).setAttribute('aria-busy', 'true'); }
  });
  document.addEventListener('htmx:afterRequest', (e) => { if (isSentence(e.target)) rowOf(e.target).setAttribute('aria-busy', 'false'); });
  document.addEventListener('htmx:beforeSwap', (e) => {
    const elt = e.detail.requestConfig && e.detail.requestConfig.elt;
    if (isSentence(elt) && e.detail.xhr.satyaSent !== elt.value) e.detail.shouldSwap = false; // stale: the text moved on
  });
  document.addEventListener('htmx:afterSettle', () => {
    $$('[data-live]').forEach((l) => { const r = rowOf(l); if (r.dataset.status !== l.dataset.status) r.dataset.status = l.dataset.status; });
    syncAnchors(); measure();
  });
  document.addEventListener('htmx:configRequest', (e) => { // Approve carries every textarea so unchecked edits get re-checked server-side
    if (e.detail.elt.matches && e.detail.elt.matches('[data-approve]')) {
      $$('textarea[data-sid]').forEach((t) => { e.detail.parameters['text-' + t.dataset.sid] = t.value; });
    }
  });
  const recheckFailed = (e) => {
    const elt = e.detail.elt || e.target;
    if (!isSentence(elt)) return;
    rowOf(elt).setAttribute('aria-busy', 'false');
    document.getElementById('err-' + elt.dataset.sid).replaceChildren($('#tpl-recheck-error').content.cloneNode(true));
    rowOf(elt).dataset.status = 'unchecked'; // counted as blocking by nextIssue; the server re-checks on Approve
  };
  document.addEventListener('htmx:sendError', recheckFailed);
  document.addEventListener('htmx:responseError', recheckFailed);

  /* Events the server sends in HX-Trigger */
  document.addEventListener('satya:say', (e) => say(val(e)));
  document.addEventListener('satya:focus', (e) => { const el = document.getElementById(val(e)); if (el) el.focus(); });
  document.addEventListener('satya:settext', (e) => { const t = document.getElementById(e.detail.id); if (t) t.value = e.detail.text; });
  document.addEventListener('satya:resolve', (e) => {
    const r = document.getElementById('s-' + val(e));
    if (r && !reduced()) { r.classList.remove('resolve'); void r.offsetWidth; r.classList.add('resolve'); }
  });
  document.addEventListener('satya:reload', () => location.reload());
  syncAnchors();
})();

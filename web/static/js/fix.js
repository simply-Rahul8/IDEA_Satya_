/* Fix with Satya: stepwise generation (start, step until done, cancel) and HTMX hooks for the claim forms. CSP-safe. */
(() => {
  'use strict';
  const { $, say } = window.satya;
  const csrf = () => (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  const post = async (url) => {
    const r = await fetch(url, { method: 'POST', headers: { 'X-CSRF-Token': csrf() }, credentials: 'same-origin' });
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  };
  const val = (e) => (typeof e.detail === 'string' ? e.detail : e.detail.value);

  document.addEventListener('alpine:init', () => {
    Alpine.data('satyaGenerate', () => ({
      pack: '',
      running: false,
      init() {
        this.pack = this.$root.dataset.pack;
        this.paint({ done: Number($('#gen-bar').getAttribute('aria-valuenow')), total: Number(this.$root.dataset.total) });
        if (this.$root.dataset.auto === '1') this.start();
      },
      url(action) { return `/packs/${this.pack}/generate/${action}`; },
      show(id, on) { const el = $(id); if (el) el.hidden = !on; },
      paint(p) {
        const bar = $('#gen-bar');
        bar.setAttribute('aria-valuenow', String(p.done));
        bar.firstElementChild.style.width = `${p.total ? Math.round((100 * p.done) / p.total) : 0}%`;
      },
      async start() {
        this.show('#gen-start', false);
        this.show('#gen-error', false);
        this.show('#gen-cancel', true);
        try { this.report(await post(this.url('start'))); } catch (e) { return this.fail(); }
        this.run();
      },
      async run() {
        if (this.running) return;
        this.running = true;
        try {
          for (;;) {
            const p = await post(this.url('step'));
            this.report(p);
            if (p.status !== 'running') break;
          }
        } catch (e) { this.fail(); }
        this.running = false;
      },
      report(p) {
        $('#gen-label').textContent = p.label;
        this.paint(p);
        if (p.status === 'running') return;
        this.show('#gen-cancel', false);
        if (p.status === 'done') { say(p.label); location.assign(p.next); return; }
        const err = $('#gen-error');
        err.textContent = p.status === 'cancelled' ? '' : p.label;
        err.hidden = p.status === 'cancelled';
        const go = $('#gen-start');
        go.textContent = 'Try again';
        go.hidden = false;
        go.focus();
        say(p.label);
      },
      fail() {
        this.show('#gen-cancel', false);
        const err = $('#gen-error');
        err.textContent = 'We lost the connection. Nothing was changed. Try again.';
        err.hidden = false;
        const go = $('#gen-start');
        go.textContent = 'Try again';
        go.hidden = false;
        say(err.textContent);
      },
      async cancel() {
        try { this.report(await post(this.url('cancel'))); } catch (e) { this.fail(); }
      },
    }));
  });

  // Rejected confirmations (422 or 403) carry the claim with its error: swap them in.
  document.addEventListener('htmx:beforeSwap', (e) => {
    const elt = e.detail.requestConfig && e.detail.requestConfig.elt;
    const s = e.detail.xhr.status;
    if ((s === 422 || s === 403) && elt && elt.closest('[data-swap-errors]')) { e.detail.shouldSwap = true; e.detail.isError = false; }
  });
  document.addEventListener('satya:say', (e) => say(val(e)));
  // After a claim is swapped, keep keyboard focus on it (the control that had it is gone).
  let lastClaim = '';
  document.addEventListener('htmx:beforeRequest', (e) => {
    const c = e.target.closest && e.target.closest('.claim');
    lastClaim = c ? c.id : '';
  });
  document.addEventListener('htmx:afterSettle', () => {
    const c = lastClaim && document.getElementById(lastClaim);
    lastClaim = '';
    if (c) (c.querySelector('[aria-invalid="true"]') || c).focus();
  });
})();

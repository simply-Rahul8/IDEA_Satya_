/* Satya web: Alpine.data components (CSP build, no inline expressions) and HTMX hooks. Strict-CSP safe. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const say = (msg) => { const el = $('#sr-status'); if (el) el.textContent = msg; };
  const fire = (el, type) => el.dispatchEvent(new Event(type, { bubbles: true }));
  const toast = (msg) => window.dispatchEvent(new CustomEvent('satya:toast', { detail: msg }));

  document.addEventListener('alpine:init', () => {
    Alpine.data('satyaTheme', () => ({
      pressed: false,
      init() { this.pressed = this.isDark(); },
      isDark() {
        const t = document.documentElement.dataset.theme;
        return t ? t === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
      },
      toggle() {
        const next = this.isDark() ? 'light' : 'dark';
        document.documentElement.dataset.theme = next;
        try { localStorage.setItem('satya-theme', next); } catch (e) { /* storage blocked */ }
        this.pressed = next === 'dark';
      },
    }));

    Alpine.data('satyaToast', () => ({
      timer: 0,
      init() {
        window.addEventListener('satya:toast', (e) => this.show(typeof e.detail === 'string' ? e.detail : e.detail.value));
        this.$el.addEventListener('mouseenter', () => clearTimeout(this.timer));
        this.$el.addEventListener('focusin', () => clearTimeout(this.timer));
      },
      show(msg) {
        this.$el.textContent = msg;
        this.$el.classList.add('is-open');
        clearTimeout(this.timer);
        this.timer = setTimeout(() => this.$el.classList.remove('is-open'), 2600);
      },
    }));

    Alpine.data('satyaCopy', () => ({
      async copy() {
        const text = this.$el.dataset.copy;
        try { await navigator.clipboard.writeText(text); const done = this.$el.dataset.done || 'Summary copied.'; say(done); toast(done); }
        catch (e) { say('Could not copy. Select the text and copy it manually.'); }
      },
    }));

    Alpine.data('satyaChecker', () => ({
      get ta() { return this.$root.querySelector('#text'); },
      mirror(e) {
        if (e.target.id !== 'text') return;
        const b = $('#backdrop-text');
        b.textContent = e.target.value + (e.target.value.endsWith('\n') ? ' ' : '');
        if (!CSS.supports('field-sizing', 'content')) { e.target.style.height = 'auto'; e.target.style.height = e.target.scrollHeight + 'px'; }
      },
      paste(e) {
        if (e.target.id !== 'text' || !e.clipboardData) return;
        e.preventDefault(); // plain text only: pasted markup is data, never interpreted (P19)
        const t = e.clipboardData.getData('text/plain');
        e.target.setRangeText(t, e.target.selectionStart, e.target.selectionEnd, 'end');
        fire(e.target, 'input');
      },
      clear() {
        this.ta.value = '';
        fire(this.ta, 'input');
        const v = $('#verdict'); if (v) v.replaceChildren();
        say('');
        this.ta.focus();
      },
      useSample() {
        this.ta.value = this.$el.dataset.sample;
        fire(this.ta, 'input');
      },
    }));
  });

  /* ---------- Citation sheet (native <dialog>) ---------- */
  let opener = null;
  const sheet = () => $('#sheet');
  const closeSheet = () => {
    const d = sheet();
    if (!d || !d.open) return;
    d.classList.remove('is-open');
    let done = false;
    const finish = () => { if (done) return; done = true; d.close(); if (opener && opener.isConnected) opener.focus(); };
    d.addEventListener('transitionend', finish, { once: true });
    setTimeout(finish, 500); // reduced motion or no transition: never leave it open
  };
  const openSheet = (btn) => {
    const d = sheet(); if (!d) return;
    opener = btn;
    $('#sheet-body').innerHTML = '<p class="skel">&nbsp;</p><p class="skel">&nbsp;</p><p class="skel">&nbsp;</p><p class="skel">&nbsp;</p>';
    d.showModal();
    requestAnimationFrame(() => d.classList.add('is-open'));
    $('#sheet-close').focus();
    const quote = btn.dataset.quote || '';
    htmx.ajax('GET', btn.dataset.sheet, { target: '#sheet-body', swap: 'innerHTML' }).then(() => {
      const q = $('#sheet-quote');
      if (q && quote) { q.textContent = quote; q.hidden = false; }
    }).catch(() => {
      $('#sheet-body').innerHTML = '<p role="alert">Could not load the rule. Close this panel and try again.</p>';
    });
  };
  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-sheet]');
    if (t) return openSheet(t);
    if (e.target.closest('#sheet-close') || e.target === sheet()) closeSheet();
  });
  document.addEventListener('cancel', (e) => { if (e.target === sheet()) { e.preventDefault(); closeSheet(); } }, true);

  /* ---------- HTMX hooks: checker ---------- */
  let marksBefore = new Set();
  let risen = false;
  const isChecker = (el) => el && el.id === 'text';
  const marks = () => new Set($$('#backdrop-text [data-key]').map((m) => m.dataset.key));
  document.addEventListener('htmx:beforeRequest', (e) => {
    if (!isChecker(e.target)) return;
    e.detail.xhr.satyaSent = e.target.value;
    const w = $('.verdict-wrap'); if (w) w.setAttribute('aria-busy', 'true');
  });
  document.addEventListener('htmx:afterRequest', (e) => {
    if (!isChecker(e.target)) return;
    const w = $('.verdict-wrap'); if (w) w.setAttribute('aria-busy', 'false');
  });
  document.addEventListener('htmx:beforeSwap', (e) => {
    const elt = e.detail.requestConfig && e.detail.requestConfig.elt;
    if (!isChecker(elt)) return;
    if (e.detail.xhr.satyaSent !== elt.value) { e.detail.shouldSwap = false; return; } // stale: the text moved on
    if (e.detail.xhr.status === 429) { e.detail.shouldSwap = true; e.detail.isError = false; }
    marksBefore = marks();
  });
  document.addEventListener('htmx:afterSettle', () => {
    $$('#backdrop-text [data-key]').forEach((m) => { if (!marksBefore.has(m.dataset.key)) m.classList.add('is-new'); });
    marksBefore = marks();
    const v = $('#verdict[data-variant]');
    if (v && !risen) { risen = true; v.classList.add('is-rising'); }
  });
  const showError = (e) => {
    if (!isChecker(e.detail.elt || e.target)) return;
    const tpl = $('#tpl-error'), v = $('#verdict');
    if (!tpl || !v) return;
    const n = document.createElement('div'); n.id = 'verdict'; n.append(tpl.content.cloneNode(true));
    v.replaceWith(n);
    const w = $('.verdict-wrap'); if (w) w.setAttribute('aria-busy', 'false');
  };
  document.addEventListener('htmx:sendError', showError);
  document.addEventListener('htmx:responseError', showError);
  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-retry]')) { const ta = $('#text'); if (ta) ta.dispatchEvent(new Event('satya:recheck')); }
  });

  window.satya = { say, reduced, toast, $, $$, fire };
})();

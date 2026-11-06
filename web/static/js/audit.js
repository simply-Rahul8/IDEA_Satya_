/* Audit screens: upload, client-driven stepping, heat-strip (roving tabindex, filter, sort, inspector). CSP-safe. */
(() => {
  'use strict';
  const { $, $$, say, reduced } = window.satya;
  const csrf = () => (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  const post = async (url) => {
    const r = await fetch(url, { method: 'POST', headers: { 'X-CSRF-Token': csrf() }, credentials: 'same-origin' });
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  };
  const NOUN = { all: 'products', red: 'blocked products', amber: 'products to review', green: 'clear products', na: 'products that were not checked' };
  const match = (cell, f) => f === 'all' || cell.dataset.s === f || (f === 'na' && (cell.dataset.s === 'skipped' || cell.dataset.s === 'error'));

  document.addEventListener('alpine:init', () => {
    Alpine.data('satyaCounter', () => ({
      init() {
        const el = this.$el, n = Number(el.dataset.n);
        if (reduced() || !n) return;
        const t0 = performance.now();
        el.textContent = '0';
        const tick = (t) => {
          const p = Math.min(1, (t - t0) / 700);
          el.textContent = String(Math.round(n * (1 - Math.pow(1 - p, 3))));
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      },
    }));

    Alpine.data('satyaAuditForm', () => ({}));

    Alpine.data('satyaDropzone', () => ({
      over() { this.$el.classList.add('is-over'); },
      leave(e) { if (!this.$el.contains(e.relatedTarget)) this.$el.classList.remove('is-over'); },
      drop(e) {
        this.$el.classList.remove('is-over');
        const files = e.dataTransfer && e.dataTransfer.files;
        if (!files || !files.length) return;
        $('#audit-file').files = files;
        this.submit();
      },
      chosen() { this.submit(); },
      submit() {
        const form = this.$el.closest('form');
        $('#audit-problem').replaceChildren();
        htmx.trigger(form, 'submit');
      },
      showPaste() {
        $('#audit-file').value = '';
        $('#pick-box').hidden = true;
        $('#paste-box').hidden = false;
        $('#audit-text').focus();
      },
      showFile() {
        $('#audit-text').value = '';
        $('#paste-box').hidden = true;
        $('#pick-box').hidden = false;
        $('#audit-problem').replaceChildren();
        $('label[for="audit-file"]').focus();
      },
    }));

    Alpine.data('satyaAudit', () => ({
      f: 'all', mode: 'sort', from: 0, busy: false, asked: -1, paused: false,
      init() {
        const d = this.$root.dataset;
        this.f = d.f;
        this.order = d.sort;
        this.job = d.job;
        this.total = Number(d.total);
        this.strip = $('#strip', this.$root);
        const bar = $('#job-bar i');
        if (bar) bar.style.width = bar.dataset.pct + '%';
        const s = this.strip;
        s.addEventListener('mouseover', (e) => { const c = e.target.closest('.cell'); if (c) this.select(c); });
        s.addEventListener('focusin', (e) => { const c = e.target.closest('.cell'); if (c) { this.rove(c); this.select(c); } });
        s.addEventListener('keydown', (e) => this.keys(e));
        s.addEventListener('click', (e) => {
          const c = e.target.closest('.cell');
          if (!c) return;
          this.select(c);
          if (e.detail > 0) e.stopPropagation(); // a pointer tap selects; Enter/Space (detail 0) falls through and opens the peek
        });
        window.addEventListener('online', () => { if (this.paused) this.resume(); });
        if (d.mode === 'running') this.run();
      },
      cells() { return Array.from(this.strip.children); },

      /* ---- selection and keyboard ---- */
      select(cell) {
        const prev = $('.cell[aria-current="true"]', this.strip);
        if (prev && prev !== cell) prev.removeAttribute('aria-current');
        cell.setAttribute('aria-current', 'true');
        const x = cell.dataset;
        $('#in-badge').replaceChildren($('#badges').content.querySelector(`[data-b="${x.s}"]`).cloneNode(true));
        $('#in-name').textContent = x.name;
        $('#in-sku').textContent = x.sku;
        $('#in-top').textContent = x.top;
        $('#in-more').textContent = Number(x.more) > 0 ? `+${x.more} more` : '';
        $('#in-report').href = `/audits/${this.job}/report#p-${x.i}`;
        $('#in-peek').dataset.sheet = x.sheet;
        $('#in-empty').hidden = true;
        $('#in-body').hidden = false;
      },
      rove(cell) {
        const old = $('.cell[tabindex="0"]', this.strip);
        if (old && old !== cell) old.tabIndex = -1;
        cell.tabIndex = 0;
      },
      keys(e) {
        const cell = e.target.closest('.cell');
        if (!cell || e.altKey || e.ctrlKey || e.metaKey) return;
        const all = this.cells();
        const cols = getComputedStyle(this.strip).gridTemplateColumns.split(' ').length || 1;
        const at = all.indexOf(cell);
        const to = {
          ArrowRight: at + 1, ArrowLeft: at - 1, ArrowDown: at + cols, ArrowUp: at - cols,
          PageDown: at + 5 * cols, PageUp: at - 5 * cols, Home: 0, End: all.length - 1,
        }[e.key];
        if (to === undefined) return;
        e.preventDefault();
        const next = all[Math.max(0, Math.min(all.length - 1, to))];
        this.rove(next);
        next.focus();
      },

      /* ---- filter and sort (client-side, mirrored to the URL and the table) ---- */
      filter(e) {
        this.f = e.currentTarget.dataset.f;
        let n = 0;
        this.cells().forEach((c) => { const ok = match(c, this.f); c.classList.toggle('dim', !ok); if (ok) n += 1; });
        $$('[data-f]', this.$root).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.f === this.f)));
        const empty = $('#in-empty');
        if (n === 0) { empty.textContent = 'No products match this filter.'; empty.hidden = false; $('#in-body').hidden = true; }
        else { empty.textContent = 'Select a square to see why.'; if (!$('.cell[aria-current="true"]', this.strip)) empty.hidden = false; }
        say(`Showing ${n} ${NOUN[this.f] || 'products'}.`);
        this.sync();
      },
      sort() {
        this.order = this.order === 'cat' ? 'risk' : 'cat';
        const key = this.order === 'cat' ? 'i' : 'r';
        this.cells().sort((a, b) => Number(a.dataset[key]) - Number(b.dataset[key])).forEach((c) => this.strip.append(c));
        $('#sort-toggle').setAttribute('aria-pressed', String(this.order === 'cat'));
        say(this.order === 'cat' ? 'Sorted in catalogue order.' : 'Sorted by risk.');
        this.sync();
      },
      sync() {
        const q = new URLSearchParams();
        if (this.f !== 'all') q.set('f', this.f);
        if (this.order === 'cat') q.set('sort', 'cat');
        history.replaceState(null, '', location.pathname + (q.toString() ? '?' + q : ''));
        htmx.ajax('GET', `/audits/${this.job}/rows?page=1&f=${this.f}&sort=${this.order}`, { target: '#rows', swap: 'innerHTML' });
      },

      /* ---- client-driven job ---- */
      progress(p) {
        const n = p.done + p.failed;
        const bar = $('#job-bar');
        bar.setAttribute('aria-valuenow', String(n));
        $('i', bar).style.width = (this.total ? (100 * n) / this.total : 0) + '%';
        $('#job-label').textContent = p.label;
        const quarter = Math.floor((4 * n) / Math.max(1, this.total));
        if (quarter !== this.asked && p.status === 'running') { this.asked = quarter; $('#job-live').textContent = p.label; }
        return n;
      },
      async pull() {
        const r = await fetch(`/audits/${this.job}/cells?from=${this.from}`, { credentials: 'same-origin' });
        if (!r.ok) throw new Error(String(r.status));
        const box = document.createElement('template');
        box.innerHTML = await r.text();
        const motion = !reduced();
        Array.from(box.content.children).forEach((fresh, k) => {
          const old = this.strip.querySelector(`.cell[data-i="${fresh.dataset.i}"]`);
          if (!old) return;
          fresh.tabIndex = old.tabIndex;
          if (old.getAttribute('aria-current')) fresh.setAttribute('aria-current', 'true');
          if (motion && k < 40) { fresh.classList.add('is-new'); fresh.style.animationDelay = `${k * 8}ms`; }
          old.replaceWith(fresh);
        });
        const wait = this.cells().filter((c) => c.dataset.s === 'pending').map((c) => Number(c.dataset.i));
        this.from = wait.length ? Math.min(...wait) : this.total;
      },
      async run() {
        if (this.busy) return;
        this.busy = true;
        this.paused = false;
        $('#job-resume').hidden = true;
        $('#job-cancel').hidden = false;
        try {
          let p;
          do {
            p = await post(`/audits/${this.job}/step`);
            await this.pull();
            this.progress(p);
          } while (p.status === 'running');
          say($('#job-label').textContent);
          location.reload();
        } catch (e) {
          if (!this.busy) return;
          this.hold();
        } finally {
          this.busy = false;
        }
      },
      hold() { // network lost or the tab slept: progress is server-side, nothing is lost
        this.paused = true;
        const n = this.cells().filter((c) => c.dataset.s !== 'pending').length;
        $('#job-label').textContent = `Paused at ${n} of ${this.total}`;
        $('#job-live').textContent = `Paused at ${n} of ${this.total}`;
        $('#job-cancel').hidden = true;
        $('#job-resume').hidden = false;
      },
      async cancel() {
        this.busy = false;
        try { await post(`/audits/${this.job}/cancel`); location.reload(); } catch (e) { this.hold(); }
      },
      async resume() {
        try { await post(`/audits/${this.job}/resume`); } catch (e) { return; }
        if (this.$root.dataset.mode === 'running') this.run(); else location.reload();
      },
    }));
  });

  /* ---------- HTMX hooks ---------- */
  document.addEventListener('htmx:beforeSwap', (e) => {
    const elt = e.detail.requestConfig && e.detail.requestConfig.elt;
    if (e.detail.xhr.status === 422 && elt && elt.closest('[data-swap-errors]')) { e.detail.shouldSwap = true; e.detail.isError = false; }
  });
  document.addEventListener('htmx:afterSettle', () => {
    const row = $('#rows tr[data-new]');
    if (row) { row.removeAttribute('data-new'); row.focus(); }
  });
  document.addEventListener('click', (e) => {
    if (!e.target.closest('[data-again]')) return;
    const inp = $('#audit-file');
    inp.value = '';
    $('#audit-problem').replaceChildren();
    inp.click();
  });
})();

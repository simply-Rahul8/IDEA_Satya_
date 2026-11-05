/* Satya prototype runtime (SAT-7). Vanilla JS, no deps, ~7 KB min.
   NOT the production engine: RULES below are a tiny illustrative stand-in so the
   screens behave realistically. Rule text and sources are DRAFT, unreviewed by the
   consultant (plan P20), and must never be read as legal guidance. */
(() => {
  'use strict';
  const S = (window.Satya = {});
  S.RULESET = 'v0.1-draft';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  S.$ = $; S.$$ = $$;
  S.esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  S.reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
  S.debounce = debounce;

  /* ---------- Icons (inline sprite; every flag pairs an icon with a label) ---------- */
  const I = {
    block: '<path d="M8.5 3h7L21 8.5v7L15.5 21h-7L3 15.5v-7z"/><path d="M8 12h8"/>',
    warn: '<path d="M12 3.5 21.5 20h-19z"/><path d="M12 10v4.5M12 17.4v.1"/>',
    ok: '<circle cx="12" cy="12" r="9"/><path d="m8 12.3 2.8 2.8 5.5-5.6"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.9v.1"/>',
    close: '<path d="M6 6l12 12M18 6 6 18"/>',
    moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    thumbdown: '<path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/>',
    anchor: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    book: '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 21.5V4.5M8 7h8"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    pencil: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  };
  S.icon = (n, cls = '') => `<svg class="ic ${cls}" aria-hidden="true" focusable="false"><use href="#i-${n}"/></svg>`;
  const sprite = () => {
    const el = document.createElement('div');
    el.innerHTML = `<svg width="0" height="0" style="position:absolute" aria-hidden="true">${Object.entries(I).map(([k, v]) => `<symbol id="i-${k}" viewBox="0 0 24 24">${v}</symbol>`).join('')}</svg>`;
    document.body.prepend(el.firstChild);
  };

  /* ---------- Theme ---------- */
  const setTheme = (t) => { document.documentElement.dataset.theme = t; try { localStorage.setItem('satya-theme', t); } catch (e) { /* file:// may block */ } };
  const initTheme = () => {
    const q = new URLSearchParams(location.search).get('theme');
    let t = q; try { t = t || localStorage.getItem('satya-theme'); } catch (e) { /* ignore */ }
    if (t === 'dark' || t === 'light') document.documentElement.dataset.theme = t;
    $$('[data-theme-toggle]').forEach((b) => {
      b.innerHTML = `<span class="sr-only">Toggle light or dark theme</span>${S.icon('moon')}`;
      b.addEventListener('click', () => {
        const dark = getComputedStyle(document.documentElement).colorScheme === 'dark';
        setTheme(dark ? 'light' : 'dark');
      });
    });
  };

  /* ---------- Illustrative rule engine (verb + condition patterns, P24) ---------- */
  const R = (sev, label, re, why, source, fix, extra) => ({ sev, label, re, why, source, fix, ...extra });
  S.RULES = {
    'DRG-01': R('red', 'Treatment or cure claim', /\b(?:cures?|treats?|heals?|reverses?)\s+(?:acne(?:\s+scars?)?|eczema|psoriasis|dandruff|pimples?|scars?)\b/gi,
      'Says the product treats or cures a skin condition. That is a drug-type claim, not a cosmetic one.', 'Cosmetic vs drug boundary, Drugs and Cosmetics Act, 1940', 'Describe how skin looks or feels, not a medical outcome.', { override: false }),
    'DMR-01': R('red', 'Named-disease claim', /\b(?:stops?|prevents?|reverses?|cures?)\s+(?:hair\s?fall|hair\s?loss|baldness|premature\s+greying|diabetes|obesity)\b/gi,
      'Claims to affect a disease or condition named in the DMR Act schedule.', 'Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954', 'Remove the claim. This rule cannot be overridden.', { override: false }),
    'FAIR-01': R('red', 'Fairness claim', /\b(?:lightens?|whitens?)\s+(?:your\s+)?skin(?:\s+tone)?|\bfair(?:er)?\s+(?:look|skin)\b|\bskin\s+whitening\b|\bfairness\b/gi,
      'Implies the product changes skin colour or makes skin fairer. Fairness claims are blocked outright.', 'Marketplace and ASCI guidance on fairness claims', 'Talk about radiance, evenness or hydration instead.', { override: false }),
    'EVD-01': R('amber', 'Needs evidence', /\b(?:dermatolog(?:ically|ist)[\s-]+(?:tested|approved)|clinically\s+(?:proven|tested))\b/gi,
      'A testing claim needs a test report reference before it can be confirmed.', 'ASCI guidance on substantiation of claims', 'Attach the test report or document ID, or remove the claim.', { override: true }),
    'ABS-01': R('amber', 'Absolute wording', /\b(?:100\s?%\s+natural|chemical[\s-]+free|toxin[\s-]+free|guaranteed|permanent(?:ly)?|instant(?:ly)?)\b/gi,
      'Absolute words are hard to substantiate and are often pulled by marketplaces.', 'ASCI guidance on absolute and misleading claims', 'Use measured wording such as "formulated without" or "visibly".', { override: true }),
    'TIME-01': R('amber', 'Time-bound result', /\bin\s+\d+\s+(?:days?|hours?|weeks?)\b/gi,
      'A fixed time-to-result implies a tested outcome.', 'ASCI guidance on results claims', 'Remove the time frame, or cite the study that supports it.', { override: true }),
  };
  S.SAMPLE = 'Our Rosewater Dew Serum cures acne scars in 7 days. Dermatologically tested and 100% natural, it brightens dull skin and lightens your skin tone for a fairer look. Gentle formula, made for acne-prone skin. Massage 3 drops onto a clean face every night.';

  S.check = (text) => {
    const t0 = performance.now();
    const found = [];
    for (const [id, r] of Object.entries(S.RULES)) {
      const re = new RegExp(r.re.source, r.re.flags);
      let m;
      while ((m = re.exec(text))) { found.push({ start: m.index, end: m.index + m[0].length, id, sev: r.sev, text: m[0] }); if (!m[0].length) re.lastIndex++; }
    }
    found.sort((a, b) => a.start - b.start || (a.sev === 'red' ? -1 : 1) - (b.sev === 'red' ? -1 : 1) || b.end - a.end);
    const spans = []; let edge = -1;
    for (const f of found) if (f.start >= edge) { spans.push(f); edge = f.end; }
    const red = spans.filter((s) => s.sev === 'red').length, amber = spans.length - red;
    const level = red >= 2 ? 5 : red === 1 ? 4 : amber >= 3 ? 3 : amber >= 1 ? 2 : 0;
    const label = ['No flagged risks', '', 'Moderate', 'Elevated', 'High', 'Severe'][level];
    return { spans, red, amber, level, label, ms: performance.now() - t0 };
  };

  /* ---------- Shared render helpers ---------- */
  const SEV = { red: ['Blocked', 'block'], amber: ['Review', 'warn'], green: ['Clear', 'ok'] };
  S.flagBadge = (sev, id) => `<span class="flag flag-${sev}">${S.icon(SEV[sev][1])}${SEV[sev][0]}${id ? ` <span class="id">${id}</span>` : ''}</span>`;
  S.meterHTML = (level) => `<div class="meter" data-level="${level}" role="img" aria-label="Severity meter, level ${level} of 5">${[1, 2, 3, 4, 5].map((n) => `<i class="${n <= level ? 'on' : ''}" style="--n:${n}"></i>`).join('')}</div>`;
  S.markHTML = (text, spans, o = {}) => {
    let out = '', at = 0;
    spans.forEach((s, i) => {
      out += S.esc(text.slice(at, s.start));
      const [lab, ic] = SEV[s.sev];
      const phrase = S.esc(text.slice(s.start, s.end));
      const attrs = o.interactive ? ` tabindex="0" role="button" aria-label="${phrase}: ${lab}, ${S.esc(S.RULES[s.id].label)}. Open citation"` : '';
      out += `<mark class="hl hl-${s.sev}${o.fresh ? ' is-new' : ''}" data-i="${i}" data-rule="${s.id}"${attrs}>${phrase}${o.icons ? `<span class="hl-ic">${S.icon(ic)}</span>` : ''}</mark>`;
      at = s.end;
    });
    return out + S.esc(text.slice(at));
  };
  S.counters = (el, to, ms = 700) => {
    if (S.reduced()) { el.textContent = to; return; }
    const t0 = performance.now();
    const step = (t) => { const p = Math.min(1, (t - t0) / ms); el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  };

  /* ---------- Toast ---------- */
  S.toast = (msg) => {
    let t = $('.toast');
    if (!t) { t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status'); document.body.append(t); }
    t.textContent = msg; t.classList.add('is-open');
    clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('is-open'), 2600);
  };

  /* ---------- Citation side sheet (right on desktop, bottom on mobile) ---------- */
  const sheet = (S.sheet = {
    el: null, scrim: null, opener: null,
    mount() {
      this.scrim = Object.assign(document.createElement('div'), { className: 'scrim' });
      this.el = document.createElement('aside');
      this.el.className = 'sheet'; this.el.setAttribute('role', 'dialog'); this.el.setAttribute('aria-modal', 'true'); this.el.setAttribute('aria-labelledby', 'sheet-title'); this.el.tabIndex = -1;
      document.body.append(this.scrim, this.el);
      this.scrim.addEventListener('click', () => this.close());
      document.addEventListener('keydown', (e) => {
        if (!this.el.classList.contains('is-open')) return;
        if (e.key === 'Escape') { this.close(); return; }
        if (e.key === 'Tab') {
          const f = $$('button,a[href],[tabindex="0"]', this.el); if (!f.length) return;
          const first = f[0], last = f[f.length - 1];
          if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
          else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
      });
    },
    open(ruleId, phrase, opener) {
      if (!this.el) this.mount();
      const r = S.RULES[ruleId]; this.opener = opener || document.activeElement;
      this.el.innerHTML = `<button class="icon-btn close" type="button" data-close aria-label="Close citation">${S.icon('close')}</button>
        <div>${S.flagBadge(r.sev, ruleId)}</div>
        <h2 id="sheet-title">${S.esc(r.label)}</h2>
        <p class="quote">&ldquo;${S.esc(phrase)}&rdquo;</p>
        <dl>
          <div><dt>Why it is flagged</dt><dd>${S.esc(r.why)}</dd></div>
          <div><dt>Source (illustrative)</dt><dd>${S.esc(r.source)}</dd></div>
          <div><dt>What to do</dt><dd>${S.esc(r.fix)}</dd></div>
          <div><dt>Can it be overridden?</dt><dd>${r.override ? 'Yes, with a written reason and evidence.' : 'No. This rule is not overridable.'}</dd></div>
        </dl>
        <p class="draft" style="margin-top:1.5rem">${S.icon('info')}<span>Draft rule set ${S.RULESET}. Wording and sources are not yet reviewed by our regulatory consultant. Not legal advice.</span></p>`;
      $('[data-close]', this.el).addEventListener('click', () => this.close());
      this.scrim.classList.add('is-open'); this.el.classList.add('is-open');
      $('[data-close]', this.el).focus();
    },
    close() {
      this.scrim.classList.remove('is-open'); this.el.classList.remove('is-open');
      if (this.opener && document.contains(this.opener)) this.opener.focus();
    },
  });

  /* ---------- Review model: sample PDP pack + Product Truth claims ---------- */
  S.CLAIMS = [
    { id: 'c1', text: 'Contains 5% niacinamide', kind: 'Ingredient', ev: 'Label photo', state: 'ok' },
    { id: 'c2', text: 'Contains Rosa damascena flower water', kind: 'Ingredient', ev: 'INCI list', state: 'ok' },
    { id: 'c3', text: 'Dermatologically tested', kind: 'Claim', ev: 'Test report: reference missing', state: 'warn' },
    { id: 'c4', text: 'Cures acne scars', kind: 'Claim', ev: 'Hard-blocked, cannot be confirmed', state: 'block' },
    { id: 'c5', text: 'Hydrating, dewy finish', kind: 'Claim', ev: 'Brand self-assessment', state: 'ok' },
    { id: 'c6', text: 'Use 3 drops nightly on clean face', kind: 'Usage', ev: 'Brand instruction', state: 'ok' },
    { id: 'c7', text: 'External use only; patch test first', kind: 'Warning', ev: 'Label photo', state: 'ok' },
  ];
  S.PDP = [
    { id: 's1', section: 'Title', type: 'Claim', anchors: ['c5'], text: 'Rosewater Dew Serum with Niacinamide: Visible Glow in 7 Days', rewrite: 'Rosewater Dew Serum with Niacinamide: A Dewy, Hydrated Finish' },
    { id: 's2', section: 'Bullet 1', type: 'Ingredient', anchors: ['c1', 'c2'], text: 'Made with 5% niacinamide and Damask rose water.', rewrite: '' },
    { id: 's3', section: 'Bullet 2', type: 'Claim', anchors: ['c3'], text: 'Dermatologically tested for sensitive skin.', rewrite: 'Dermatologically tested. Test report reference to be attached.' },
    { id: 's4', section: 'Bullet 3', type: 'Claim', anchors: [], text: 'Lightens your skin tone for a fairer look.', rewrite: 'Leaves skin looking radiant and even with a dewy finish.' },
    { id: 's5', section: 'Bullet 4', type: 'Claim', anchors: ['c4'], text: 'Cures acne scars with regular use.', rewrite: 'Helps skin look smoother and more even with regular use.' },
    { id: 's6', section: 'How to use', type: 'Usage', anchors: ['c6'], text: 'Apply 3 drops to a clean face every night, then moisturiser.', rewrite: '' },
    { id: 's7', section: 'Warnings', type: 'Warning', anchors: ['c7'], text: 'For external use only. Patch test before first use.', rewrite: '' },
  ];
  S.review = () => {
    const sents = S.PDP.map((s) => ({ ...s })), ack = {}, reported = {};
    const byId = (id) => sents.find((s) => s.id === id);
    const api = {
      sents, ack, reported, byId,
      result: (id) => S.check(byId(id).text),
      status(id) {
        const r = S.check(byId(id).text);
        return r.red ? 'red' : r.amber ? (ack[id] ? 'ack' : 'amber') : 'ok';
      },
      summary() {
        const c = { red: 0, amber: 0, ack: 0, ok: 0, total: sents.length };
        sents.forEach((s) => c[api.status(s.id)]++);
        c.approvable = c.red === 0 && c.amber === 0;
        return c;
      },
      edit(id, text) { byId(id).text = text; delete ack[id]; },
      apply(id) { const s = byId(id); if (s.rewrite) { s.text = s.rewrite; delete ack[id]; } },
    };
    return api;
  };
  const SENT_LABEL = { red: ['red', 'Blocked'], amber: ['amber', 'Needs a reason'], ack: ['green', 'Kept with reason'], ok: ['green', 'Clear'] };
  S.sentBadge = (st) => S.flagBadge(SENT_LABEL[st][0]).replace(/(<\/svg>)[^<]+/, `$1${SENT_LABEL[st][1]}`);

  /* Flag panel: the reusable "what is wrong, why, fix" block used by every review variant. */
  S.flagPanelHTML = (rev, s) => {
    const r = rev.result(s.id), st = rev.status(s.id);
    if (!r.spans.length) return `<p class="fp-ok">${S.flagBadge('green')} <span>No flagged risks under rule set ${S.RULESET}.</span></p>`;
    const items = r.spans.map((sp, i) => `<li class="fp-item fp-${sp.sev}">
        <div class="fp-head">${S.flagBadge(sp.sev, sp.id)}<strong>${S.esc(S.RULES[sp.id].label)}</strong></div>
        <p class="fp-why"><q>${S.esc(sp.text)}</q>. ${S.esc(S.RULES[sp.id].why)}</p>
        <button class="btn btn-ghost btn-sm" type="button" data-act="cite" data-sid="${s.id}" data-i="${i}">${S.icon('book')} Citation</button>
      </li>`).join('');
    const rw = s.rewrite && (r.red || r.amber) ? `<div class="fp-rw"><span class="eyebrow">Suggested rewrite</span><p>${S.esc(s.rewrite)}</p><button class="btn btn-primary btn-sm" type="button" data-act="apply" data-sid="${s.id}">${S.icon('check')} Use rewrite</button></div>` : '';
    const reason = !r.red && r.amber ? `<div class="fp-reason"><label class="lbl" for="rs-${s.id}">Reason to keep this wording <span class="muted">(required)</span></label>
        <div class="fp-row"><input class="field" id="rs-${s.id}" data-reason="${s.id}" value="${S.esc(rev.ack[s.id] || '')}" placeholder="e.g. test report TR-2291 attached" aria-describedby="rse-${s.id}"><button class="btn btn-secondary btn-sm" type="button" data-act="ack" data-sid="${s.id}">Keep with reason</button></div>
        <p class="fp-err" id="rse-${s.id}" role="alert"></p></div>` : '';
    const block = r.red ? `<p class="fp-note">${S.icon('block')} Blocked sentences stop approval. Rewrite or remove.</p>` : '';
    const rep = `<button class="btn btn-ghost btn-sm" type="button" data-act="report" data-sid="${s.id}" aria-pressed="${!!rev.reported[s.id]}">${S.icon('thumbdown')} ${rev.reported[s.id] ? 'Reported as wrong flag' : 'Wrong flag?'}</button>`;
    return `<ul class="fp-list">${items}</ul>${block}${rw}${reason}<div class="fp-foot">${rep}</div>`;
  };

  /* Wire a review root: shared behaviour, variants only change markup around it. */
  S.bindReview = (root, rev, hooks = {}) => {
    const refresh = (sid, o = {}) => {
      const s = rev.byId(sid), st = rev.status(sid);
      const box = $(`[data-flags="${sid}"]`, root); if (box) box.innerHTML = S.flagPanelHTML(rev, s);
      $$(`[data-sent="${sid}"]`, root).forEach((el) => { el.dataset.status = st; if (o.resolved) { el.classList.remove('resolve'); void el.offsetWidth; el.classList.add('resolve'); } });
      $$(`[data-badge="${sid}"]`, root).forEach((el) => { el.innerHTML = S.sentBadge(st); });
      const txt = $(`[data-edit="${sid}"]`, root);
      if (txt && (o.rewrite || o.blur)) txt.innerHTML = S.markHTML(s.text, rev.result(sid).spans, { icons: true });
      S.updateSummary(root, rev); if (hooks.after) hooks.after(sid, st);
    };
    const live = debounce((el) => {
      const sid = el.dataset.edit; rev.edit(sid, el.textContent);
      const ms = rev.result(sid).ms; refresh(sid);
      $$('[data-recheck]', root).forEach((n) => { n.textContent = `Re-checked in ${Math.max(1, Math.round(ms))} ms`; });
    }, 120);
    root.addEventListener('input', (e) => { const el = e.target.closest('[data-edit]'); if (el) live(el); });
    root.addEventListener('focusout', (e) => { const el = e.target.closest('[data-edit]'); if (el) { rev.edit(el.dataset.edit, el.textContent); refresh(el.dataset.edit, { blur: true }); } });
    root.addEventListener('click', (e) => {
      const b = e.target.closest('[data-act]'); if (!b) return;
      const sid = b.dataset.sid || (b.closest('[data-sent]') || {}).dataset?.sent, act = b.dataset.act;
      if (act === 'cite') { const sp = rev.result(sid).spans[+b.dataset.i]; S.sheet.open(sp.id, sp.text, b); }
      if (act === 'apply') { rev.apply(sid); refresh(sid, { rewrite: true, resolved: true }); S.toast('Rewrite applied. Re-checked, no flagged risks.'); }
      if (act === 'ack') {
        const inp = $(`[data-reason="${sid}"]`, root), v = inp.value.trim();
        if (!v) { inp.focus(); $(`#rse-${sid}`, root).textContent = 'Add a reason to keep amber wording.'; $(`[data-reason="${sid}"]`, root).setAttribute('aria-invalid', 'true'); return; }
        rev.ack[sid] = v; refresh(sid, { resolved: true }); S.toast('Kept with your reason. It will travel with the audit record.');
      }
      if (act === 'report') { rev.reported[sid] = true; refresh(sid); S.toast('Thanks. Sent to the tuning queue.'); }
      if (act === 'anchor') S.focusClaim(root, b.dataset.claim, b, hooks);
    });
    S.updateSummary(root, rev);
    return { refresh };
  };
  S.updateSummary = (root, rev) => {
    const c = rev.summary();
    $$('[data-sum]', root).forEach((n) => { n.textContent = c[n.dataset.sum]; });
    $$('[data-approve]', root).forEach((b) => {
      b.setAttribute('aria-disabled', String(!c.approvable));
      b.onclick = (e) => { e.preventDefault(); if (c.approvable) S.toast('Approved. Audit record attached to export.'); else S.toast(`${c.red} blocked and ${c.amber} needing a reason. Resolve them to approve.`); };
    });
    $$('[data-approve-note]', root).forEach((n) => {
      n.innerHTML = c.approvable ? `${S.icon('ok')} Ready to approve. No flagged risks under rule set ${S.RULESET}.` : `${S.icon(c.red ? 'block' : 'warn')} ${c.red ? `${c.red} blocked` : ''}${c.red && c.amber ? ' and ' : ''}${c.amber ? `${c.amber} need${c.amber === 1 ? 's' : ''} a reason` : ''} before you can approve.`;
    });
  };
  S.focusClaim = (root, cid, from, hooks = {}) => {
    const on = from && from.getAttribute('aria-pressed') !== 'true';
    $$('[data-claim]', root).forEach((n) => n.classList.remove('is-source'));
    $$('[data-act="anchor"]', root).forEach((n) => n.setAttribute('aria-pressed', 'false'));
    $$('[data-sent]', root).forEach((n) => n.classList.remove('is-linked'));
    if (!on) return;
    from.setAttribute('aria-pressed', 'true');
    const tgt = $$(`[data-claim="${cid}"]`, root);
    tgt.forEach((n) => n.classList.add('is-source'));
    $$('[data-act="anchor"]', root).filter((n) => n.dataset.claim === cid).forEach((n) => n.setAttribute('aria-pressed', 'true'));
    if (hooks.onClaim) hooks.onClaim(cid, tgt);
    const vis = tgt.find((n) => n.offsetParent !== null);
    if (vis) vis.scrollIntoView({ block: 'nearest', behavior: S.reduced() ? 'auto' : 'smooth' });
    const live = $('#claim-live', root); if (live) live.textContent = `Source claim highlighted: ${S.CLAIMS.find((c) => c.id === cid).text}`;
  };
  S.claimStateBadge = (st) => ({ ok: S.flagBadge('green').replace(/(<\/svg>)[^<]+/, '$1Confirmed'), warn: S.flagBadge('amber').replace(/(<\/svg>)[^<]+/, '$1Needs reference'), block: S.flagBadge('red').replace(/(<\/svg>)[^<]+/, '$1Cannot confirm') }[st]);

  /* ---------- Boot ---------- */
  S.ready = (fn) => (document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', fn) : fn());
  S.ready(() => { sprite(); initTheme(); });
})();

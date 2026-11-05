# ADR-10: What "0 red in exports" means, and a strict-CSP frontend

Status: accepted (CTO, SAT-13 review). Rule content and wording stay draft until consultant sign-off (P20).

## Context
Plan §10 says "0 🔴 in exports". The draft rules (`engine/rules/cosmetic_claims.yaml`, e.g. EN-CLAIM-001) include reds with `overridable: true`, where a brand can keep a claim by attaching evidence. The final specs (SAT-13) support both readings via `allow_red_override`.

## Decision
1. **"0 🔴 in exports" means zero *unresolved* reds.** An export may contain a red only if it is overridable, carries a reason and an evidence reference, and is recorded in the audit ledger under the rule-set version. Non-overridable rules (drug/treatment, DMR Act diseases, fairness) never export, and no override control renders for them (P17, ADR-9 `check_override`). The UI therefore ships with `allow_red_override = true` for overridable reds only.
2. Overridden reds count towards the override rate (plan §10: under 15%), and the audit export lists them separately. They are never styled green: "kept with reason" has its own neutral-with-warning state (spec: review B).
3. If the consultant makes EN-CLAIM-001 non-overridable (open question in the rule file), this needs no UI change: the flag simply loses its control.
4. **Strict CSP is a build constraint.** Alpine uses the CSP build (`@alpinejs/csp`, no inline expressions, components registered with `Alpine.data`) and HTMX runs with `allowEval: false`. No inline `<script>` or `style=""` in templates. Spec examples that use inline expressions are illustrative and must be rewritten as registered components.

## Consequences
- Frontend (SAT-21) builds to these. A render test asserts no inline script/style and that severity classes survive the Tailwind purge.
- Open items routed out of the specs: engine payload fields (`anchor_state`, sentence `type`, `suggested_rewrite`) go to the Engine owner; Legal Metrology severity and whether the public checker runs the product-type gate go to the Rules owner (default: amber `LM-` ids; the checker does run the gate, `needs_review` shown as "we can't tell"); "nothing stored" copy does not ship until Platform confirms it, and the checker cap and rate limits are set there.

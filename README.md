# Content Bench — Stripe Connect proof (`v0.1-stripe-proof`)

Public, brand-clean proof that a docs engine can **generate**, **humanize**,
**gate**, **measure**, and **improve** integration pages — without pasting from
raw sources and without claiming to be Stripe.

Quote the parity result as **15 of 15 parity checks**, not “identical to Stripe.”

## The five-part story

### 1. Generated from spec

Connect reference pages and the onboarding quickstart are rendered from a local
OpenAPI fixture plus Connect prose guides. Nothing is hand-pasted into
`content/`.

```bash
python3 pipelines/run_stripe_connect_proof.py
python3 pipelines/run_reference_pages_a2.py   # Payment Gateway fixture pages (separate lane)
```

Published pages: `content/connect-*.md`.

### 2. Gated by a human (A3)

Prose goes through `write_prose` → `humanize` against
[`style/customer-voice.md`](style/customer-voice.md) (ten rules). Templated
facts live in `<!-- section:facts -->` and are protected by `fact_hash`.

Proof the humanizer cannot change a fact:

`tests/test_humanizer.py::HumanizerTests.test_humanizer_cannot_change_templated_fact`

```bash
python3 pipelines/write_prose.py
python3 pipelines/humanize.py
python3 -m unittest tests.test_humanizer
```

Every page still merges only via PR.

### 3. Proven by a task eval

An eval walks the generated Connect docs and either:

- **mock** — asserts required onboarding facts are present (PR gate), or
- **live** — creates a real test-mode connected account + Account Link with a
  `sk_test_` key (demo claim).

```bash
python3 evals/run_connect_eval.py --mode mock
STRIPE_TEST_SECRET_KEY=sk_test_... python3 evals/run_connect_eval.py --mode live
```

Frozen live trace: [`evals/evidence/v0.1-stripe-proof/connect-live.md`](evals/evidence/v0.1-stripe-proof/connect-live.md)
([JSON](evals/evidence/v0.1-stripe-proof/connect-live.json)).

**Live gate: pass** on the Samaya Stripe test platform (`acct_1TzhSHD…`).
Generated docs still teach Accounts v1 controller fields (parity with public
Stripe docs). The Samaya sandbox disables new v1 account creation, so the live
eval falls back to Accounts v2 (same path as `~/workspace/stripe-quickstart`),
then creates a v1 Account Link. Mock gate remains **pass**.

### 4. Measured against live upstream

Nightly (and on demand) we fetch public Stripe docs and score our Connect pages.

Frozen result: [`evals/evidence/v0.1-stripe-proof/parity-15-of-15.md`](evals/evidence/v0.1-stripe-proof/parity-15-of-15.md)
— **15 of 15** graded checks, fidelity score 100.0% on that checklist.

```bash
python3 evals/run_stripe_docs_compare.py --evidence
```

Parity is **evidence only**, never a PR gate. Nightly reports push to
`evidence/stripe-docs-parity` (not `main`).

### 5. Improved from evidence

Failed eval steps and parity gaps feed the next regen from sources — never
hand-edits to `content/`. After `v0.1-stripe-proof`, the Stripe lane takes
**no new features**; only the nightly parity job keeps running as a freshness
demo. New scope goes to the CyberSource lane in the private repo.

## Invariants

- Serve layers (portal, MCP, humanizer, evals) read `content/` + `normalized/` only — never `raw/`.
- Task eval may gate PRs; parity eval must not.
- No secrets or PAN in traces (`_redact` on live runs).
- Engine fixes made privately port back here the same day; private corpus never lands in this repo.

## Quick start

```bash
python3 -m unittest discover -s tests
python3 evals/run_connect_eval.py --mode mock
python3 scripts/check_content_render.py
cd mcp-server && npm install   # content-docs MCP — see mcp-server/README.md
node portal/server.js          # http://127.0.0.1:8787/connect-quickstart
```

## Also in this repo

Earlier Content Bench workflow-contract prototypes (Flex / Microform / HTTP
Signature) remain under `pipelines/run_demo.py` and `reports/`. The Stripe
Connect lane above is the public end-to-end proof of the content engine.

## Plans

- `docs/plans/2026-08-07-002-feat-stripe-connect-proof-plan.md`
- `docs/plans/2026-08-07-003-feat-a2-reference-pages-plan.md`
- `docs/plans/2026-08-07-004-feat-a3-humanizer-plan.md`

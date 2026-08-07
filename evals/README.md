# Evals

- **Task eval (PR gate):** `python3 evals/run_connect_eval.py --mode mock`
- **Task eval (live demo):** `STRIPE_TEST_SECRET_KEY=sk_test_... python3 evals/run_connect_eval.py --mode live`
  (falls back to `STRIPE_SECRET_KEY` when that value is already `sk_test_`)
- **Stripe docs parity (evidence only, never a PR gate):** `python3 evals/run_stripe_docs_compare.py --evidence`
- **Humanizer fact guard (unit):** `python3 -m unittest tests.test_humanizer` — proves A3 cannot change templated facts

Regenerable scratch (`evals/runs/*.json`, `evals/latest.md`,
`evals/stripe-docs-compare.md`) is gitignored so ad-hoc runs do not dirty the
tree. Nightly parity pushes to `evidence/stripe-docs-parity`.

Frozen wrap-up snapshots for the Stripe proof live under
[`evals/evidence/v0.1-stripe-proof/`](evidence/v0.1-stripe-proof/) (committed).

# Evals

- **Task eval (PR gate):** `python3 evals/run_connect_eval.py --mode mock`
- **Stripe docs parity (evidence only, never a PR gate):** `python3 evals/run_stripe_docs_compare.py --evidence`

Parity reports are always regenerated. The nightly workflow pushes them to the
`evidence/stripe-docs-parity` branch (and uploads a CI artifact). Local runs
write `evals/stripe-docs-compare.md`, which is gitignored so test/ad-hoc runs
do not dirty the working tree.

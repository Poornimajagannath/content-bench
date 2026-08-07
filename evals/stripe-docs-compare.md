# Stripe docs comparison eval

- When: `2026-08-07T04:45:17+00:00`
- Scope: generated `content/connect-*.md` vs live Stripe Connect docs
- Fidelity score: **100.0%** (15 pass / 0 partial / 0 fail of 15 graded checks)

## Sources fetched

- `accounts_create` → https://docs.stripe.com/api/accounts/create (HTTP 200)
- `account_links_create` → https://docs.stripe.com/api/account_links/create (HTTP 200)
- `onboarding_quickstart` → https://docs.stripe.com/connect/onboarding/quickstart (HTTP 200)
- `how_connect_works` → https://docs.stripe.com/connect/how-connect-works (HTTP 200)

## Checks

| ID | Area | Result | Notes |
| --- | --- | --- | --- |
| `links_path` | Account Links API | **pass** | Path matches official Account Links create docs. |
| `links_required_fields` | Account Links API | **pass** | All required fields present. |
| `links_type_onboarding` | Account Links API | **pass** | Matches Stripe's primary onboarding link type. |
| `links_expiry_guidance` | Account Links API | **pass** | We mention expiry; Stripe is more specific about refresh_url behavior. |
| `links_collection_options` | Account Links API | **pass** | Aligned when our sources include collection_options with currently_due/eventually_due. |
| `accounts_path` | Accounts API | **pass** | Endpoint path still correct. |
| `accounts_create_shape` | Accounts API | **pass** | Pass when generated accounts page leads with controller and marks type deprecated. |
| `accounts_capabilities` | Accounts API | **pass** | Aligned at a high level; we do not enumerate full capability matrix. |
| `auth_secret_key` | Auth | **pass** | Semantically aligned (platform secret key). Transport encoding differs (Bearer vs Stripe's classic -u Basic); both accepted by Stripe API. |
| `auth_no_live_keys` | Auth | **pass** | Good sandbox discipline for our proof lane. |
| `flow_steps` | Onboarding flow | **pass** | Core backend track matches. Official UI also covers frontend samples & dashboard properties we omit. |
| `webhooks` | Onboarding flow | **pass** | Pass when webhook confirmation replaces polling-only guidance. |
| `embedded_vs_hosted` | Onboarding flow | **pass** | Scoped hosted Account Links proof is intentional; not graded as incomplete coverage. |
| `provenance` | Provenance | **pass** | We correctly label pages as generated from a local fixture — not a Stripe mirror. |
| `a2_not_stripe` | Scope control | **pass** | A2 reference pages are out of scope for Stripe fidelity; do not grade them as Stripe docs. |

## Verdict

Parity gate **pass** at 100.0%. Controller-first accounts create, Account Links `collection_options`, and `account.updated` webhook confirmation are present in generated Connect pages.

A2 `createPayment` pages are **not Stripe docs** and were excluded from the score.
This parity eval is nightly evidence only — it must not gate PRs.

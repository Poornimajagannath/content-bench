# Stripe docs comparison eval

- When: `2026-08-07T04:36:47+00:00`
- Scope: generated `content/connect-*.md` vs live Stripe Connect docs
- Fidelity score: **80.0%** (11 pass / 2 partial / 2 fail of 15 graded checks)

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
| `links_collection_options` | Account Links API | **fail** | Gap: official API documents collection_options; our fixture pages omit it. |
| `accounts_path` | Accounts API | **pass** | Endpoint path still correct. |
| `accounts_create_shape` | Accounts API | **partial** | Drift: Stripe's published create example now leads with controller properties; type=express still appears in older Connect guides and often still works, but our page does not teach the controller-based create shape. |
| `accounts_capabilities` | Accounts API | **pass** | Aligned at a high level; we do not enumerate full capability matrix. |
| `auth_secret_key` | Auth | **pass** | Semantically aligned (platform secret key). Transport encoding differs (Bearer vs Stripe's classic -u Basic); both accepted by Stripe API. |
| `auth_no_live_keys` | Auth | **pass** | Good sandbox discipline for our proof lane. |
| `flow_steps` | Onboarding flow | **pass** | Core backend track matches. Official UI also covers frontend samples & dashboard properties we omit. |
| `webhooks` | Onboarding flow | **fail** | Gap: no webhook guidance in generated pages. |
| `embedded_vs_hosted` | Onboarding flow | **partial** | Scoped proof (hosted Account Links) is intentional; not a full Connect guide. |
| `provenance` | Provenance | **pass** | We correctly label pages as generated from a local fixture — not a Stripe mirror. |
| `a2_not_stripe` | Scope control | **pass** | A2 reference pages are out of scope for Stripe fidelity; do not grade them as Stripe docs. |

## Verdict

Our Connect proof docs are **directionally correct** for a narrow backend onboarding track (platform test secret → `POST /v1/accounts` → `POST /v1/account_links` with `account_onboarding` → verify account). Account Links required fields match the live API docs.

Main fidelity gaps vs current Stripe docs:

1. **Accounts create shape drift** — Stripe's current create example leads with `controller[...]`; we still teach classic `type=express` + capabilities.
2. **Missing `collection_options`** on Account Links.
3. **No webhooks** (`account.updated`) or embedded-components / Accounts v2 coverage (acceptable for a scoped proof, incomplete as a Stripe guide).

A2 `createPayment` pages are **not Stripe docs** and were excluded from the score.

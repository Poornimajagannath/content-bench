---
source_url: https://docs.stripe.com/connect/onboarding/quickstart
title: Connect onboarding quickstart
---

# Connect onboarding quickstart

Goal: create a connected account and send the user through hosted onboarding via an Account Link.

## Prerequisites

- Connect enabled on your platform in test mode.
- Platform test secret key.
- Public `return_url` and `refresh_url` you control.

## Steps

1. Create a connected account with `country` and the `controller[...]` shape:
   `controller[fees][payer]`, `controller[losses][payments]`, and
   `controller[stripe_dashboard][type]` (for example `express`).
   The legacy `type` parameter is deprecated; prefer `controller` for new integrations.
2. Create an Account Link of type `account_onboarding` for that account id.
   Optionally set `collection_options[fields]` to `currently_due` (default) or `eventually_due`.
3. Redirect the user to the Account Link `url`.
4. Listen for `account.updated` and check `charges_enabled` / `details_submitted`
   instead of polling. During development you may also `GET /v1/accounts/{account}`.

## Expected outcome

You have an `acct_...` id and the connected account completed (or started) onboarding through Stripe-hosted flow.

## Common errors

- Missing `refresh_url` or `return_url` on Account Links → 400.
- Creating Account Links with a non-platform key → 401.

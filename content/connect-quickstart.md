---
title: Stripe Connect onboarding quickstart
generated: true
product: stripe-connect
---

# Stripe Connect onboarding quickstart

<!-- section:prose -->
## Overview

Follow these steps to create a connected account and an Account Link with your platform test secret key.

<!-- TODO: Confirm any product-specific prerequisites with the owning team. -->
<!-- /section:prose -->

<!-- section:facts -->

## 1. Prepare platform test credentials

**Goal:** Authenticate as the Connect platform in test mode.

**Prerequisites**
- Stripe account with Connect enabled in test mode
- Environment variable STRIPE_TEST_SECRET_KEY=sk_test_...

**Actions**
1. Confirm the key prefix is sk_test_ (never sk_live_ for this proof).
2. Send Authorization: Bearer $STRIPE_TEST_SECRET_KEY on platform calls.

**Expected outcome:** API requests authenticate without 401.

**Common errors**
- 401 when using a publishable key or missing Bearer header

## 2. Create a connected account

**Goal:** Obtain an acct_... id for onboarding.

**Prerequisites**
- Platform test secret key

**Actions**
1. POST /v1/accounts with country plus controller[fees][payer], controller[losses][payments], and controller[stripe_dashboard][type] (e.g. express).
2. Request capabilities such as card_payments and transfers when required by your integration.
3. Deprecated alternative: the type parameter still exists but prefer controller fields instead of type.
4. Store the returned account id.

**Expected outcome:** Response includes id starting with acct_.

**Common errors**
- 400 when country or required controller fields are missing
- 401 when the platform key is invalid

## 3. Create an Account Link

**Goal:** Send the connected account through Stripe-hosted onboarding.

**Prerequisites**
- Connected account id from step 2
- HTTPS return_url and refresh_url you control

**Actions**
1. POST /v1/account_links with account, type=account_onboarding, return_url, refresh_url.
2. Example: set collection_options[fields]=currently_due (or eventually_due) when you need that collection mode.
3. Redirect the user to the url field in the response.
4. If the link expires, create a new Account Link for the same account.

**Expected outcome:** Response includes a single-use url and expires_at.

**Common errors**
- 400 when return_url/refresh_url/type are missing
- 401 when not using the platform secret key

## 4. Confirm onboarding via webhook

**Goal:** Learn when the connected account finished submitting details without polling.

**Prerequisites**
- Account id
- Webhook endpoint receiving Connect events

**Actions**
1. Listen for account.updated on your webhook endpoint.
2. On account.updated, check charges_enabled and details_submitted instead of polling GET /v1/accounts/{account}.

**Expected outcome:** Webhook payload shows onboarding progress (details_submitted / charges_enabled).

**Common errors**
- Missing Connect webhook signing secret configuration
- Ignoring account.updated and relying only on return_url

<!-- /section:facts -->

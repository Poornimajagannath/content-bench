---
title: POST /v1/accounts
generated: true
source: openapi-connect.fixture.json
---

# POST /v1/accounts

**Method:** `POST`  
**Path:** `/v1/accounts`  
**Operation ID:** `PostAccounts`

## Auth

Platform secret key via HTTP Bearer (`sk_test_...` in test mode).
Security: `[{"bearerAuth": []}]`

## Parameters

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| Stripe-Version | header | False | string |  |
| country | body | True | string | Two-letter country code |
| email | body | False | string | Email for the connected account |
| controller[fees][payer] | body | True | string | Who pays Stripe fees (controller pattern) |
| controller[losses][payments] | body | True | string | Who is liable for negative balances (controller pattern) |
| controller[stripe_dashboard][type] | body | True | string | Dashboard access for the connected account (controller pattern) |
| capabilities[card_payments][requested] | body | False | boolean | Request card_payments capability |
| capabilities[transfers][requested] | body | False | boolean | Request transfers capability |
| type | body | False | string | Deprecated. Prefer controller[stripe_dashboard][type] and related controller fields instead of type. |

## Status codes

`200`, `400`, `401`

## Notes

Create a connected account

<!-- section: generated -->

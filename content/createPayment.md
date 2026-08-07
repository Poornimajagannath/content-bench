---
title: Create a payment authorization
generated: true
source: doc-payments-core-openapi
operation_id: createPayment
lineage_origin: generated_from_spec
---

# Create a payment authorization

**Method:** `POST`  
**Path:** `/pts/v2/payments`  
**Operation ID:** `createPayment`

## Auth

Required scheme(s) from the OpenAPI fixture: `httpSignature`.

## Request

### Body fields

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| CreatePaymentRequest | object | yes |  |

## Response

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| Payment | object |  | Success schema Payment |

## Errors

- `error_schema`: Error payload shaped by ErrorResponse — recovery: Inspect reason/details; fix request or auth; retry in sandbox only

## Evidence (from spec)

> "Create a payment authorization"

> "Authorize a payment in sandbox using tokenized or instrument identifiers. Do not send raw PAN."

## Related workflows

`microform-payer-auth-state-machine`

## Provenance

- `lineage_origin`: `generated_from_spec`
- `unit_id`: `payments-core-openapi:ref:createPayment`
- `api_name`: Payment Gateway Payments Core (local Content Bench fixture)

Every fact on this page traces to the OpenAPI-derived reference unit. Sandbox only — do not use production credentials from these docs.

<!-- section: generated -->

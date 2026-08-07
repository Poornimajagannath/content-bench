---
title: Create a credit
generated: true
source: doc-payments-core-openapi
operation_id: createCredit
lineage_origin: generated_from_spec
---

# Create a credit

**Method:** `POST`  
**Path:** `/pts/v2/credits`  
**Operation ID:** `createCredit`

## Auth

Required scheme(s) from the OpenAPI fixture: `httpSignature`.

## Request

### Body fields

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| CreditRequest | object | yes |  |

## Response

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| Payment | object |  | Success schema Payment |

## Errors

- `error_schema`: Error payload shaped by ErrorResponse — recovery: Inspect reason/details; fix request or auth; retry in sandbox only

## Evidence (from spec)

> "Create a credit"

## Related workflows

`microform-payer-auth-state-machine`

## Provenance

- `lineage_origin`: `generated_from_spec`
- `unit_id`: `payments-core-openapi:ref:createCredit`
- `api_name`: Payment Gateway Payments Core (local Content Bench fixture)

Every fact on this page traces to the OpenAPI-derived reference unit. Sandbox only — do not use production credentials from these docs.

<!-- section: generated -->

---
title: Capture an authorized payment
generated: true
source: doc-payments-core-openapi
operation_id: capturePayment
lineage_origin: generated_from_spec
---

# Capture an authorized payment

**Method:** `POST`  
**Path:** `/pts/v2/payments/{id}/captures`  
**Operation ID:** `capturePayment`

## Auth

Required scheme(s) from the OpenAPI fixture: `httpSignature`.

## Request

### Path parameters

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| id | string | yes | Path parameter id |

### Body fields

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| clientReferenceInformation.code | string | no |  |
| orderInformation.amountDetails.totalAmount | string | yes |  |
| orderInformation.amountDetails.currency | string | no |  |

## Response

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| id | string | no |  |
| status | string | no |  |

## Errors

- `error_schema`: Error payload shaped by ErrorResponse — recovery: Inspect reason/details; fix request or auth; retry in sandbox only

## Evidence (from spec)

> "Capture an authorized payment"

## Related workflows

`microform-payer-auth-state-machine`

## Provenance

- `lineage_origin`: `generated_from_spec`
- `unit_id`: `payments-core-openapi:ref:capturePayment`
- `api_name`: Payment Gateway Payments Core (local Content Bench fixture)

Every fact on this page traces to the OpenAPI-derived reference unit. Sandbox only — do not use production credentials from these docs.

<!-- section: generated -->

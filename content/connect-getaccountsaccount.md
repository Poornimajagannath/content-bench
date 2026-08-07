---
title: GET /v1/accounts/{account}
generated: true
source: openapi-connect.fixture.json
---

# GET /v1/accounts/{account}

<!-- section:prose -->
## Overview

You call `GET /v1/accounts/{account}` when you need this Connect operation.

<!-- TODO: Add a short customer-facing example once sandbox samples are approved. -->
<!-- /section:prose -->

<!-- section:facts -->
**Method:** `GET`  
**Path:** `/v1/accounts/{account}`  
**Operation ID:** `GetAccountsAccount`

## Auth

Platform secret key via HTTP Bearer (`sk_test_...` in test mode).
Security: `[{"bearerAuth": []}]`

## Parameters

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| account | path | True | string |  |

## Status codes

`200`, `401`, `404`

## Notes

Retrieve a connected account

<!-- /section:facts -->

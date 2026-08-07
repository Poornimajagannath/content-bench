---
title: POST /v1/account_links
generated: true
source: openapi-connect.fixture.json
---

# POST /v1/account_links

<!-- section:prose -->
## Overview

You call `POST /v1/account_links` when you need this Connect operation.

<!-- TODO: Add a short customer-facing example once sandbox samples are approved. -->
<!-- /section:prose -->

<!-- section:facts -->
**Method:** `POST`  
**Path:** `/v1/account_links`  
**Operation ID:** `PostAccountLinks`

## Auth

Platform secret key via HTTP Bearer (`sk_test_...` in test mode).
Security: `[{"bearerAuth": []}]`

## Parameters

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| account | body | True | string | Connected account id |
| refresh_url | body | True | string | URL if the link expires |
| return_url | body | True | string | URL after onboarding |
| type | body | True | string | Link purpose |
| collection_options[fields] | body | False | string | Which requirements to collect. Example: currently_due (default) vs eventually_due. |
| collection_options[future_requirements] | body | False | string | Whether to collect future_requirements (default omit). |

## Status codes

`200`, `400`, `401`

## Notes

Create an Account Link for onboarding

<!-- /section:facts -->

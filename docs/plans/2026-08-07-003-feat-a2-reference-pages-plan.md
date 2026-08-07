# Plan: A2 reference pages from OpenAPI units

**Date:** 2026-08-07  
**Status:** Implemented on `cursor/a2-reference-pages-0af3`

## Goal

Turn the eight `api_reference_unit` drafts in
`artifacts/content_engine/generated/payments-core-openapi.api_reference_units.json`
into published `content/<operationId>.md` pages the portal and content-docs MCP can serve.

## Approach

1. Read units with `lineage_origin: generated_from_spec` only (fail if otherwise).
2. Render method, path, auth, request/response fields, errors, evidence quotes, provenance.
3. Write filenames as `{operation_id}.md` so MCP `get_page("createPayment")` resolves.
4. Record `artifacts/content_engine/a2/reference-pages-summary.json`.

## Out of scope

Humanizer (A3), nightly loop (A4), live tempo agent evals (B1+).

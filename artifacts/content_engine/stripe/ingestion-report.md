# Ingestion report

Milestone 0.5: corpus cleaned at the door. `raw/` is immutable evidence; serve layers read only `normalized/` and `content/`.

- Stamp date: `2026-08-06`
- Docs fetched into raw: 4
- Claims extracted: 30
- Raw dir: `raw/2026-08-06`
- Normalized file: `normalized/2026-08-06.claims.json`
- Read contract: normalized/, content/
- Forbidden: raw/

## Claims by schema

| Schema | Count |
| --- | ---: |
| quickstart_step | 10 |
| endpoint_fact | 6 |
| error_case | 0 |
| prose_claim | 14 |

## Drop log

| Path | Reason | Detail |
| --- | --- | --- |
| 2026-08-06/account-links.md | no_schema_match | no quickstart/endpoint/error/prose claim extracted |
| 2026-08-06/openapi-connect.fixture.json | no_schema_match | no quickstart/endpoint/error/prose claim extracted |

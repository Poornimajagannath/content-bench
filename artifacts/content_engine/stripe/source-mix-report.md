# Source mix report

Milestone 0 inventory: what fraction of each guide's facts could be regenerated from the local OpenAPI fixture versus facts that exist only in prose.

- OpenAPI: `data/stripe/openapi-connect.fixture.json`
- Guides sampled: 4
- Overall spec-backed share: **79.8%**
- Overall prose-only share: **20.2%**
- Decision rule outcome: spec-primary: generate endpoint pages from OpenAPI; DocETL mines prose only for gaps

## Per-guide table

| Guide | Spec-backed | Prose-only | Spec hits | Prose hits | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| account-links | 83.3% | 16.7% | 5 | 1 | — |
| connect-authentication | 70.0% | 30.0% | 7 | 3 | — |
| how-connect-works | 75.0% | 25.0% | 9 | 3 | — |
| onboarding-quickstart | 90.9% | 9.1% | 10 | 1 | — |

## Top 10 prose-only sections for a first integration

_No prose-dominant sections found in the sample._

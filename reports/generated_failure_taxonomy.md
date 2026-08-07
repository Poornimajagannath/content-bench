# Generated failure taxonomy (V0 routing)

Routing lives in `content_bench/routing.py`. Categories are deterministic for the three V0 workflows.

| Workflow | Failure category | Typical evidence | Primary surfaces |
|----------|------------------|------------------|------------------|
| `flex-token-lifecycle` | `token-lifecycle-confusion` | Persist transient JWT; skip TMS instrument create | docs, content_cli |
| `http-signature-debug` | `auth-mechanism` | `keyId`/`secretKey` vs SDK fields; wrong host; incomplete signed headers | docs, sdk, content_cli |
| `microform-payer-auth-state-machine` | `state-machine-gap` | Skip enrollment/challenge/validation; missing auth refs | docs, content_cli, mcp |

## Severity defaults (V0)

- Docs clarification: **high** when stage order is wrong
- SDK field-name drift (HTTP Signature): **high**
- Content CLI workflow verifier recommendation: **high**
- MCP grounding hint: included for Microform/Payer Auth

## Content CLI descriptor bias

When routing to `content_cli`, the action carries a workflow-verifier descriptor:

- goal
- command
- API/SDK facts
- readiness checks
- recovery path
- support-safe evidence
- telemetry/eval hints
- future MCP metadata

V0 emits recommendations / fixture checks only — no live credentials.

## How to regenerate

```bash
python3 pipelines/run_bench_v0.py --workflow microform-payer-auth-state-machine
```

Inspect `artifacts/reports/<workflow>.report.json` → `classification.actions`.

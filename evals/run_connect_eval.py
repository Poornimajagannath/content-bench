#!/usr/bin/env python3
"""Stripe Connect eval gate: mock (CI) or live test-mode Account + Account Link."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
RUNS = ROOT / "evals" / "runs"
LATEST = ROOT / "evals" / "latest.md"

REQUIRED_QUICKSTART_MARKERS = (
    "STRIPE_TEST_SECRET_KEY",
    "POST /v1/accounts",
    "POST /v1/account_links",
    "account_onboarding",
    "sk_test_",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _redact(text: str) -> str:
    text = re.sub(r"sk_(test|live)_[A-Za-z0-9]+", "sk_***REDACTED***", text)
    text = re.sub(r"Bearer\s+\S+", "Bearer ***REDACTED***", text)
    return text


def run_mock() -> Dict[str, Any]:
    quickstart = CONTENT / "connect-quickstart.md"
    steps: List[Dict[str, Any]] = []
    if not quickstart.exists():
        return {
            "mode": "mock",
            "gate": "fail",
            "reason": "content/connect-quickstart.md missing — run pipelines/run_stripe_connect_proof.py",
            "steps": [],
        }
    body = quickstart.read_text(encoding="utf-8")
    missing = [m for m in REQUIRED_QUICKSTART_MARKERS if m not in body]
    steps.append(
        {
            "step": "docs_gate",
            "result": "pass" if not missing else "fail",
            "detail": "ok" if not missing else f"missing markers: {missing}",
        }
    )
    pages = list(CONTENT.glob("connect-*.md"))
    steps.append(
        {
            "step": "fact_pages",
            "result": "pass" if pages else "fail",
            "detail": f"{len(pages)} connect-*.md pages",
        }
    )
    gate = "pass" if not missing and pages else "fail"
    return {
        "mode": "mock",
        "gate": gate,
        "reason": "generated Connect docs contain required onboarding facts",
        "steps": steps,
        "at": _utc_now(),
    }


# Samaya sandbox / stripe-quickstart use Accounts v2 (API version from stripe-node).
STRIPE_V2_VERSION = "2026-07-29.dahlia"
STRIPE_V2_VERSION_FALLBACK = "2025-11-17.preview"


def _require_test_secret(secret: str) -> None:
    if not secret.startswith("sk_test_"):
        raise ValueError("Live eval requires a test-mode key (sk_test_...). Refusing other key types.")


def _stripe_request(
    path: str,
    secret: str,
    *,
    method: str = "POST",
    fields: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    stripe_version: Optional[str] = None,
) -> Tuple[int, Dict[str, Any], str]:
    _require_test_secret(secret)
    headers = {"Authorization": f"Bearer {secret}"}
    data: Optional[bytes] = None
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body).encode("utf-8")
    elif fields is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = urllib.parse.urlencode(fields).encode("utf-8")
    if stripe_version:
        headers["Stripe-Version"] = stripe_version
    req = urllib.request.Request(
        f"https://api.stripe.com{path}",
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"error": {"message": raw[:500]}}
        return exc.code, payload, raw


def _stripe_form(
    path: str,
    secret: str,
    fields: Dict[str, str],
) -> Tuple[int, Dict[str, Any], str]:
    return _stripe_request(path, secret, fields=fields)


def _v1_accounts_disabled(payload: Dict[str, Any]) -> bool:
    msg = str((payload.get("error") or {}).get("message") or payload)
    return "Accounts v1" in msg and "feat_accounts_v1_support" in msg


def _create_account_v2(secret: str) -> Tuple[int, Dict[str, Any], str, str]:
    """Create a connected account the Samaya sandbox way (Accounts v2)."""
    body = {
        "display_name": "content-bench live eval",
        "contact_email": "content-bench-eval@example.com",
        "dashboard": "express",
        "defaults": {
            "responsibilities": {
                "fees_collector": "application",
                "losses_collector": "application",
            }
        },
        "identity": {"country": "US"},
        "configuration": {
            "recipient": {
                "capabilities": {
                    "stripe_balance": {"stripe_transfers": {"requested": True}}
                }
            },
            "merchant": {
                "capabilities": {"card_payments": {"requested": True}}
            },
        },
        "include": [
            "configuration.merchant",
            "configuration.recipient",
            "identity",
            "defaults",
        ],
    }
    for version in (STRIPE_V2_VERSION, STRIPE_V2_VERSION_FALLBACK):
        status, account, raw = _stripe_request(
            "/v2/core/accounts",
            secret,
            json_body=body,
            stripe_version=version,
        )
        if status in (200, 201) and str(account.get("id", "")).startswith("acct_"):
            return status, account, raw, version
    return status, account, raw, version


def run_live(secret: str) -> Dict[str, Any]:
    """Live gate against the Samaya Stripe test platform.

    Prefer Accounts v1 (matches generated Connect docs). If the platform has
    disabled v1 creation — Samaya sandbox default — fall back to Accounts v2
    as used by ~/workspace/stripe-quickstart, then create a v1 Account Link.
    """
    steps: List[Dict[str, Any]] = []
    api_used = "v1"

    status, account, _raw = _stripe_form(
        "/v1/accounts",
        secret,
        {
            "country": "US",
            "controller[fees][payer]": "application",
            "controller[losses][payments]": "application",
            "controller[stripe_dashboard][type]": "express",
            "capabilities[card_payments][requested]": "true",
            "capabilities[transfers][requested]": "true",
        },
    )
    if status == 200 and str(account.get("id", "")).startswith("acct_"):
        steps.append(
            {
                "step": "create_account",
                "result": "pass",
                "api": "v1",
                "http_status": status,
                "account_id": account.get("id"),
                "detail": account.get("id"),
            }
        )
    elif _v1_accounts_disabled(account):
        status, account, _raw, version = _create_account_v2(secret)
        api_used = "v2"
        ok_create = status in (200, 201) and str(account.get("id", "")).startswith(
            "acct_"
        )
        steps.append(
            {
                "step": "create_account",
                "result": "pass" if ok_create else "fail",
                "api": "v2",
                "stripe_version": version,
                "http_status": status,
                "account_id": account.get("id"),
                "detail": _redact(
                    json.dumps(
                        {
                            "fallback": "Accounts v1 disabled on platform; used Samaya v2 path",
                            "error_or_id": account.get("error", account.get("id")),
                        }
                    )
                ),
            }
        )
        if not ok_create:
            return {
                "mode": "live",
                "gate": "fail",
                "reason": "account creation failed (v1 disabled; v2 fallback failed)",
                "platform": "samaya-sandbox",
                "steps": steps,
                "at": _utc_now(),
            }
    else:
        steps.append(
            {
                "step": "create_account",
                "result": "fail",
                "api": "v1",
                "http_status": status,
                "account_id": account.get("id"),
                "detail": _redact(json.dumps(account.get("error", account))),
            }
        )
        return {
            "mode": "live",
            "gate": "fail",
            "reason": "account creation failed",
            "steps": steps,
            "at": _utc_now(),
        }

    status2, link, _raw2 = _stripe_form(
        "/v1/account_links",
        secret,
        {
            "account": account["id"],
            "refresh_url": "https://example.com/reauth",
            "return_url": "https://example.com/return",
            "type": "account_onboarding",
        },
    )
    ok = status2 == 200 and bool(link.get("url"))
    steps.append(
        {
            "step": "create_account_link",
            "result": "pass" if ok else "fail",
            "api": "v1",
            "http_status": status2,
            "has_url": bool(link.get("url")),
            "detail": _redact(
                json.dumps(link.get("error", {"expires_at": link.get("expires_at")}))
            ),
        }
    )
    return {
        "mode": "live",
        "gate": "pass" if ok else "fail",
        "reason": (
            f"created connected account ({api_used}) + Account Link in Samaya test mode"
            if ok
            else "Account Link creation failed"
        ),
        "platform": "samaya-sandbox",
        "account_api": api_used,
        "steps": steps,
        "at": _utc_now(),
    }


def write_outputs(
    result: Dict[str, Any],
    *,
    latest_path: Optional[Path] = None,
    runs_dir: Optional[Path] = None,
) -> Path:
    """Write run JSON + latest markdown. Defaults are gitignored scratch outputs."""
    out_runs = Path(runs_dir) if runs_dir is not None else RUNS
    out_latest = Path(latest_path) if latest_path is not None else LATEST
    out_runs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = out_runs / f"connect-{result['mode']}-{stamp}.json"
    safe = json.loads(_redact(json.dumps(result)))
    run_path.write_text(json.dumps(safe, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Connect eval latest",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Gate: **{result['gate']}**",
        f"- When: {result.get('at', '')}",
        f"- Reason: {result.get('reason', '')}",
        "",
        "## Steps",
        "",
        "| Step | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for step in result.get("steps") or []:
        lines.append(
            f"| {step.get('step')} | {step.get('result')} | {_redact(str(step.get('detail', '')))} |"
        )
    lines.append("")
    out_latest.parent.mkdir(parents=True, exist_ok=True)
    out_latest.write_text("\n".join(lines), encoding="utf-8")
    return out_latest


def main() -> int:
    parser = argparse.ArgumentParser(description="Stripe Connect eval gate")
    parser.add_argument("--mode", choices=("mock", "live"), default="mock")
    args = parser.parse_args()

    if args.mode == "mock":
        result = run_mock()
    else:
        secret = os.environ.get("STRIPE_TEST_SECRET_KEY", "").strip()
        if not secret:
            # Allow STRIPE_SECRET_KEY when it is already a test-mode key.
            fallback = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            if fallback.startswith("sk_test_"):
                secret = fallback
        if not secret:
            print(
                "STRIPE_TEST_SECRET_KEY not set "
                "(or STRIPE_SECRET_KEY sk_test_ fallback)",
                file=sys.stderr,
            )
            return 2
        try:
            result = run_live(secret)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    write_outputs(result)
    print(json.dumps({k: result[k] for k in ("mode", "gate", "reason")}, indent=2))
    print(f"Wrote {LATEST}")
    return 0 if result.get("gate") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

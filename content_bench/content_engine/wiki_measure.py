"""Phase-zero wiki measurement — score arbitrary markdown pages without claim ids.

Reads a folder of already-written pages (wiki, portal export, hand-authored docs)
and reports quality metrics using the same heuristics as the content engine,
without requiring provenance, claim ids, or normalized claims.

Metrics per page (every number carries its denominator):
  - workflow/quickstart steps with vs without a stated outcome
  - API endpoints with vs without required fields (CyberSource pattern + A2 tables)
  - pages with vs without a source pointer (URL or path to upstream)
  - drift vs live upstream when a source URL is present (parity-style checks)
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from content_bench.content_engine.api_reference import (
    _parse_required_fields,
    _REQ_FIELDS_HEADING,
    _VERB_URL,
    extract_api_reference_claims,
)

# ---------------------------------------------------------------------------
# Step / outcome detection (no claim ids)
# ---------------------------------------------------------------------------

_OUTCOME_MISSING_FLAG = re.compile(
    r"^\s*-\s*outcome_missing:\s*(true|false)\s*$", re.M | re.I
)
_EXPECTED_OUTCOME_LINE = re.compile(
    r"(?m)^\s*(?:-\s*)?\*\*Expected outcome:\*\*\s*(.+)$"
)
_QUICKSTART_STEP = re.compile(r"(?m)^##\s+(\d+)\.\s+(.+)$")
_NUMBERED_STEP = re.compile(r"(?m)^(\d+)\.\s+\*\*(.+?)\*\*")
_GAP_OUTCOME = re.compile(r"\*\*Gap:\*\*|not stated", re.I)

# UI prose outcome heuristics (from workflow_pages._expected_outcome)
_UI_OUTCOME_IN_ACTION = re.compile(
    r"(?:The|A|An)\s+[^.]*\b(?:page|window|dialog|menu|list)\b[^.]*\bappears[^.]*\.",
    re.I,
)
_UI_DISPLAYED = re.compile(r"[^.]*\bis displayed\b[^.]*\.", re.I)


@dataclass
class StepMeasure:
    step_index: int
    label: str
    has_stated_outcome: bool
    detection: str  # explicit_flag | expected_outcome_heading | action_heuristic | gap_marker | none


@dataclass
class EndpointMeasure:
    method: str
    path: str
    has_required_fields: bool
    has_rest_example: bool
    detection: str  # api_reference_pattern | a2_reference | inline_verb_path


@dataclass
class ParityCheck:
    check_id: str
    result: str  # pass | partial | fail | n/a
    signal: str
    ours: str
    upstream: str
    notes: str


@dataclass
class PageScorecard:
    rel_path: str
    steps_total: int
    steps_with_outcome: int
    steps_without_outcome: int
    step_details: List[StepMeasure] = field(default_factory=list)
    endpoints_total: int = 0
    endpoints_with_required_fields: int = 0
    endpoints_without_required_fields: int = 0
    endpoint_details: List[EndpointMeasure] = field(default_factory=list)
    has_source_pointer: bool = False
    source_pointers: List[str] = field(default_factory=list)
    parity_checks: List[ParityCheck] = field(default_factory=list)
    parity_score: Optional[float] = None
    parity_graded: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["step_details"] = [asdict(s) for s in self.step_details]
        d["endpoint_details"] = [asdict(e) for e in self.endpoint_details]
        d["parity_checks"] = [asdict(p) for p in self.parity_checks]
        return d


@dataclass
class WikiMeasureReport:
    wiki_root: str
    measured_at: str
    pages_total: int
    pages_with_source_pointer: int
    pages_without_source_pointer: int
    steps_total: int
    steps_with_outcome: int
    steps_without_outcome: int
    endpoints_total: int
    endpoints_with_required_fields: int
    endpoints_without_required_fields: int
    parity_pages_with_checks: int
    parity_score: Optional[float]
    pages: List[PageScorecard] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wiki_root": self.wiki_root,
            "measured_at": self.measured_at,
            "aggregate": {
                "pages_total": self.pages_total,
                "pages_with_source_pointer": self.pages_with_source_pointer,
                "pages_without_source_pointer": self.pages_without_source_pointer,
                "steps_total": self.steps_total,
                "steps_with_outcome": self.steps_with_outcome,
                "steps_without_outcome": self.steps_without_outcome,
                "endpoints_total": self.endpoints_total,
                "endpoints_with_required_fields": self.endpoints_with_required_fields,
                "endpoints_without_required_fields": self.endpoints_without_required_fields,
                "parity_pages_with_checks": self.parity_pages_with_checks,
                "parity_score": self.parity_score,
            },
            "pages": [p.to_dict() for p in self.pages],
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _outcome_from_action(action: str) -> Optional[str]:
    m = _UI_OUTCOME_IN_ACTION.search(action)
    if m:
        return m.group(0).strip()
    m = _UI_DISPLAYED.search(action)
    if m:
        return m.group(0).strip()
    return None


def _is_stated_outcome(text: str) -> bool:
    t = text.strip()
    if not t or _GAP_OUTCOME.search(t):
        return False
    return True


def measure_steps(text: str) -> List[StepMeasure]:
    """Detect workflow/quickstart steps and whether each has a stated outcome."""
    steps: List[StepMeasure] = []

    # Engine-generated workflow pages: group by numbered step blocks.
    for m in _NUMBERED_STEP.finditer(text):
        idx = int(m.group(1))
        label = m.group(2).strip()
        block_start = m.start()
        next_m = _NUMBERED_STEP.search(text, m.end())
        block_end = next_m.start() if next_m else len(text)
        block = text[block_start:block_end]

        flag_m = _OUTCOME_MISSING_FLAG.search(block)
        if flag_m:
            missing = flag_m.group(1).lower() == "true"
            steps.append(
                StepMeasure(
                    step_index=idx,
                    label=label,
                    has_stated_outcome=not missing,
                    detection="explicit_flag",
                )
            )
            continue

        eo_m = _EXPECTED_OUTCOME_LINE.search(block)
        if eo_m:
            steps.append(
                StepMeasure(
                    step_index=idx,
                    label=label,
                    has_stated_outcome=_is_stated_outcome(eo_m.group(1)),
                    detection="expected_outcome_heading",
                )
            )
            continue

        action_m = re.search(r"(?m)^\s*-\s*Action[s]?:\s*(.+)$", block)
        action = action_m.group(1) if action_m else block
        inferred = _outcome_from_action(action)
        steps.append(
            StepMeasure(
                step_index=idx,
                label=label,
                has_stated_outcome=inferred is not None,
                detection="action_heuristic" if inferred else "none",
            )
        )

    if steps:
        return steps

    # Quickstart sections: ## N. Title … **Expected outcome:**
    for m in _QUICKSTART_STEP.finditer(text):
        idx = int(m.group(1))
        label = m.group(2).strip()
        block_start = m.start()
        next_m = _QUICKSTART_STEP.search(text, m.end())
        block_end = next_m.start() if next_m else len(text)
        block = text[block_start:block_end]

        eo_m = _EXPECTED_OUTCOME_LINE.search(block)
        if eo_m:
            steps.append(
                StepMeasure(
                    step_index=idx,
                    label=label,
                    has_stated_outcome=_is_stated_outcome(eo_m.group(1)),
                    detection="expected_outcome_heading",
                )
            )
        else:
            steps.append(
                StepMeasure(
                    step_index=idx,
                    label=label,
                    has_stated_outcome=False,
                    detection="none",
                )
            )

    return steps


# ---------------------------------------------------------------------------
# Endpoint / required-fields detection
# ---------------------------------------------------------------------------

_A2_METHOD = re.compile(r"(?m)^\*\*Method:\*\*\s*`?(GET|POST|PUT|PATCH|DELETE)`?", re.I)
_A2_PATH = re.compile(r"(?m)^\*\*Path:\*\*\s*`?(/[^\s`]+)`?", re.I)
_TABLE_REQUIRED_COL = re.compile(
    r"(?m)^\|\s*Name\s*\|\s*Type\s*\|\s*Required\s*\|"
)


def _scan_a2_reference_endpoints(text: str) -> List[EndpointMeasure]:
    """A2-style reference pages: **Method:** / **Path:** + body-fields table."""
    method_m = _A2_METHOD.search(text)
    path_m = _A2_PATH.search(text)
    if not method_m or not path_m:
        return []

    has_rf = False
    if _TABLE_REQUIRED_COL.search(text):
        # Count rows where Required column is "yes"
        in_table = False
        for line in text.splitlines():
            if _TABLE_REQUIRED_COL.match(line):
                in_table = True
                continue
            if in_table and line.startswith("|") and "---" not in line:
                cols = [c.strip() for c in line.strip("|").split("|")]
                if len(cols) >= 3 and cols[2].lower() in ("yes", "required", "true"):
                    has_rf = True
                    break
            elif in_table and line.strip() and not line.startswith("|"):
                break

    return [
        EndpointMeasure(
            method=method_m.group(1).upper(),
            path=path_m.group(1).strip(),
            has_required_fields=has_rf,
            has_rest_example="```" in text,
            detection="a2_reference",
        )
    ]


def _scan_inline_verb_paths(text: str, *, skip_spans: Sequence[Tuple[int, int]] = ()) -> List[EndpointMeasure]:
    """Fallback: POST /v1/accounts style lines outside Endpoint blocks."""
    found: List[EndpointMeasure] = []
    seen: set = set()
    for m in _VERB_URL.finditer(text):
        if any(s <= m.start() < e for s, e in skip_spans):
            continue
        method = m.group(1).upper()
        path = m.group(3).rstrip(".,;")
        key = f"{method}:{path}"
        if key in seen:
            continue
        seen.add(key)
        # Look for Required Fields nearby (±800 chars)
        window = text[max(0, m.start() - 200) : m.end() + 800]
        has_rf = bool(_REQ_FIELDS_HEADING.search(window)) or bool(
            re.search(r"(?i)required field", window)
        )
        has_ex = "```" in window
        found.append(
            EndpointMeasure(
                method=method,
                path=path,
                has_required_fields=has_rf,
                has_rest_example=has_ex,
                detection="inline_verb_path",
            )
        )
    return found


def measure_endpoints(text: str, *, rel_path: str) -> List[EndpointMeasure]:
    """Endpoints via CyberSource api_reference pattern, A2 tables, or inline paths."""
    endpoints: List[EndpointMeasure] = []
    skip_spans: List[Tuple[int, int]] = []
    seen: set = set()

    _, report, _ = extract_api_reference_claims(
        text,
        source_pointer=rel_path,
        doc_stem=Path(rel_path).stem,
    )
    if report.matched:
        for match in re.finditer(r"(?m)^(?:#{1,6}\s+)?Endpoint\b", text):
            block_start = match.start()
            next_ep = re.search(r"(?m)^(?:#{1,6}\s+)?Endpoint\b", text[match.end() :])
            block_end = match.end() + next_ep.start() if next_ep else len(text)
            skip_spans.append((block_start, block_end))
            block = text[block_start:block_end]
            vm = _VERB_URL.search(block)
            if not vm:
                continue
            method, path = vm.group(1).upper(), vm.group(3).rstrip(".,;")
            key = (method, path)
            if key in seen:
                continue
            seen.add(key)
            req_m = _REQ_FIELDS_HEADING.search(block)
            has_rf = False
            if req_m:
                body = block[req_m.end() :]
                has_rf = bool(_parse_required_fields(body))
            has_ex = "REST Example" in block and "```" in block
            endpoints.append(
                EndpointMeasure(
                    method=method,
                    path=path,
                    has_required_fields=has_rf,
                    has_rest_example=has_ex,
                    detection="api_reference_pattern",
                )
            )

    a2 = _scan_a2_reference_endpoints(text)
    if a2:
        for ep in a2:
            key = (ep.method, ep.path)
            if key not in seen:
                seen.add(key)
                endpoints.append(ep)
    else:
        for ep in _scan_inline_verb_paths(text, skip_spans=skip_spans):
            key = (ep.method, ep.path)
            if key not in seen:
                seen.add(key)
                endpoints.append(ep)

    return endpoints


# ---------------------------------------------------------------------------
# Source pointer detection
# ---------------------------------------------------------------------------

_SOURCE_LINE = re.compile(
    r"(?m)^(?:#\s*)?Source:\s*(https?://\S+|[^\s]+/\S+)"
)
_FRONTMATTER_URL = re.compile(
    r"(?m)^(?:source|canonical_url|url):\s*(https?://\S+|[^\n]+)$", re.I
)
_HTTP_URL = re.compile(r"https?://[^\s)\]>\"']+")
_DOCS_HOST = re.compile(
    r"https?://(?:docs\.stripe\.com|developer\.cybersource\.com)[^\s)\]>\"']*"
)


def extract_source_pointers(text: str) -> List[str]:
    """URLs or paths pointing at upstream documentation."""
    found: List[str] = []
    seen: set = set()

    def add(raw: str) -> None:
        u = raw.strip().rstrip(".,;")
        if u and u not in seen:
            seen.add(u)
            found.append(u)

    # YAML frontmatter (first --- block)
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    if fm:
        for m in _FRONTMATTER_URL.finditer(fm.group(1)):
            add(m.group(1))

    for m in _SOURCE_LINE.finditer(text):
        add(m.group(1))

    # Provenance / lineage sections — prefer vendor doc hosts
    for m in _DOCS_HOST.finditer(text):
        add(m.group(0))

    if not found:
        for m in _HTTP_URL.finditer(text[:3000]):
            add(m.group(0))

    return found


# ---------------------------------------------------------------------------
# Parity / drift vs live upstream
# ---------------------------------------------------------------------------

FetchFn = Callable[[str], Tuple[int, str]]


def _default_fetch(url: str, timeout: int = 30) -> Tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "content-bench-wiki-measure/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return 0, f"FETCH_ERROR: {exc}"


def _extract_drift_signals(text: str) -> List[Tuple[str, str]]:
    """(check_id, needle) pairs to search for in live upstream HTML."""
    signals: List[Tuple[str, str]] = []
    for ep in measure_endpoints(text, rel_path=""):
        key = f"{ep.method.lower()}_{ep.path.replace('/', '_').strip('_')}"
        signals.append((f"endpoint_path_{key}", ep.path))
        signals.append((f"endpoint_verb_{key}", ep.method))

    for m in re.finditer(r"(?m)^\*\*Expected outcome:\*\*\s*(.+)$", text):
        outcome = m.group(1).strip()
        if _is_stated_outcome(outcome) and len(outcome) > 12:
            slug = re.sub(r"[^a-z0-9]+", "_", outcome[:40].lower()).strip("_")
            signals.append((f"outcome_{slug}", outcome[:80]))

    # Required field names from A2 tables
    in_table = False
    for line in text.splitlines():
        if _TABLE_REQUIRED_COL.match(line):
            in_table = True
            continue
        if in_table and line.startswith("|") and "---" not in line:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 3 and cols[2].lower() in ("yes", "required", "true"):
                name = cols[0].split(".")[-1]
                signals.append((f"field_{name}", name))
        elif in_table and line.strip() and not line.startswith("|"):
            in_table = False

    return signals


def parity_drift_checks(
    wiki_text: str,
    *,
    source_urls: Sequence[str],
    fetch_fn: Optional[FetchFn] = None,
) -> Tuple[List[ParityCheck], Optional[float]]:
    """Compare wiki page signals against live upstream (parity-style)."""
    fetch = fetch_fn or _default_fetch
    checks: List[ParityCheck] = []
    signals = _extract_drift_signals(wiki_text)

    if not source_urls:
        checks.append(
            ParityCheck(
                check_id="source_pointer",
                result="n/a",
                signal="source_url",
                ours="none",
                upstream="n/a",
                notes="No source pointer on page — drift check skipped.",
            )
        )
        return checks, None

    live_text = ""
    live_status = 0
    chosen_url = ""
    for url in source_urls:
        if not url.startswith("http"):
            continue
        live_status, live_text = fetch(url)
        chosen_url = url
        if live_status == 200 and live_text and not live_text.startswith("FETCH_ERROR"):
            break

    if live_status != 200 or not live_text or live_text.startswith("FETCH_ERROR"):
        checks.append(
            ParityCheck(
                check_id="upstream_fetch",
                result="n/a",
                signal=chosen_url or source_urls[0],
                ours=f"{len(signals)} drift signals extracted",
                upstream=f"HTTP {live_status}",
                notes="Could not fetch live upstream — drift n/a.",
            )
        )
        return checks, None

    live_lower = live_text.lower()
    for cid, needle in signals:
        present = needle.lower() in live_lower
        checks.append(
            ParityCheck(
                check_id=cid,
                result="pass" if present else "fail",
                signal=needle,
                ours="present in wiki page",
                upstream="present in live" if present else "missing in live",
                notes=f"Drift check against {chosen_url}",
            )
        )

    graded = [c for c in checks if c.result in ("pass", "partial", "fail")]
    if not graded:
        return checks, None
    score = sum(1.0 if c.result == "pass" else 0.5 if c.result == "partial" else 0.0 for c in graded)
    return checks, round(score / len(graded) * 100, 1)


def _scorecard_from_page(
    rel_path: str,
    text: str,
    *,
    fetch_fn: Optional[FetchFn] = None,
    skip_parity: bool = False,
) -> PageScorecard:
    steps = measure_steps(text)
    endpoints = measure_endpoints(text, rel_path=rel_path)
    sources = extract_source_pointers(text)

    parity_checks: List[ParityCheck] = []
    parity_score: Optional[float] = None
    if not skip_parity:
        parity_checks, parity_score = parity_drift_checks(
            text,
            source_urls=sources,
            fetch_fn=fetch_fn,
        )

    steps_with = sum(1 for s in steps if s.has_stated_outcome)
    ep_with_rf = sum(1 for e in endpoints if e.has_required_fields)

    return PageScorecard(
        rel_path=rel_path,
        steps_total=len(steps),
        steps_with_outcome=steps_with,
        steps_without_outcome=len(steps) - steps_with,
        step_details=steps,
        endpoints_total=len(endpoints),
        endpoints_with_required_fields=ep_with_rf,
        endpoints_without_required_fields=len(endpoints) - ep_with_rf,
        endpoint_details=endpoints,
        has_source_pointer=bool(sources),
        source_pointers=sources,
        parity_checks=parity_checks,
        parity_score=parity_score,
        parity_graded=sum(
            1 for c in parity_checks if c.result in ("pass", "partial", "fail")
        ),
    )


def measure_wiki_folder(
    wiki_root: Path,
    *,
    fetch_fn: Optional[FetchFn] = None,
    skip_parity: bool = False,
    exclude_readme: bool = True,
) -> WikiMeasureReport:
    """Score every *.md file under wiki_root recursively."""
    wiki_root = wiki_root.resolve()
    pages: List[PageScorecard] = []

    for path in sorted(wiki_root.rglob("*.md")):
        name = path.name.lower()
        if exclude_readme and name == "readme.md":
            continue
        rel = str(path.relative_to(wiki_root))
        text = path.read_text(encoding="utf-8", errors="replace")
        pages.append(
            _scorecard_from_page(
                rel,
                text,
                fetch_fn=fetch_fn,
                skip_parity=skip_parity,
            )
        )

    parity_scores = [p.parity_score for p in pages if p.parity_score is not None]
    agg_parity = round(sum(parity_scores) / len(parity_scores), 1) if parity_scores else None

    return WikiMeasureReport(
        wiki_root=str(wiki_root),
        measured_at=_utc_now(),
        pages_total=len(pages),
        pages_with_source_pointer=sum(1 for p in pages if p.has_source_pointer),
        pages_without_source_pointer=sum(1 for p in pages if not p.has_source_pointer),
        steps_total=sum(p.steps_total for p in pages),
        steps_with_outcome=sum(p.steps_with_outcome for p in pages),
        steps_without_outcome=sum(p.steps_without_outcome for p in pages),
        endpoints_total=sum(p.endpoints_total for p in pages),
        endpoints_with_required_fields=sum(p.endpoints_with_required_fields for p in pages),
        endpoints_without_required_fields=sum(p.endpoints_without_required_fields for p in pages),
        parity_pages_with_checks=sum(1 for p in pages if p.parity_graded > 0),
        parity_score=agg_parity,
        pages=pages,
    )


def render_scorecard_md(report: WikiMeasureReport) -> str:
    """Human-readable aggregate + per-page scorecard."""
    a = report.to_dict()["aggregate"]
    lines = [
        "# Wiki measurement scorecard (phase zero)",
        "",
        f"- Measured at: `{report.measured_at}`",
        f"- Wiki root: `{report.wiki_root}`",
        "",
        "## Aggregate (every number with denominator)",
        "",
        f"- Pages: **{a['pages_total']}** scored",
        f"- Source pointer: **{a['pages_with_source_pointer']}/{a['pages_total']}** pages",
        f"- Steps with stated outcome: **{a['steps_with_outcome']}/{a['steps_total']}**",
        f"- Steps without stated outcome: **{a['steps_without_outcome']}/{a['steps_total']}**",
        f"- Endpoints with required fields: **{a['endpoints_with_required_fields']}/{a['endpoints_total']}**",
        f"- Endpoints without required fields: **{a['endpoints_without_required_fields']}/{a['endpoints_total']}**",
    ]
    if a["parity_score"] is not None:
        lines.append(
            f"- Live-site drift (parity): **{a['parity_score']}%** "
            f"across **{a['parity_pages_with_checks']}** pages with graded checks"
        )
    else:
        lines.append("- Live-site drift (parity): **n/a** (no fetchable source URLs or offline mode)")

    lines.extend(["", "## Per-page", ""])
    for p in report.pages:
        lines.append(f"### `{p.rel_path}`")
        lines.append("")
        if p.steps_total:
            lines.append(
                f"- Outcomes: **{p.steps_with_outcome}/{p.steps_total}** steps with stated outcome"
            )
        if p.endpoints_total:
            lines.append(
                f"- Required fields: **{p.endpoints_with_required_fields}/{p.endpoints_total}** endpoints"
            )
        src = "yes" if p.has_source_pointer else "no"
        lines.append(f"- Source pointer: **{src}**")
        if p.source_pointers:
            for u in p.source_pointers[:3]:
                lines.append(f"  - `{u}`")
        if p.parity_score is not None:
            lines.append(f"- Drift score: **{p.parity_score}%** ({p.parity_graded} checks)")
        lines.append("")

    return "\n".join(lines)


def write_report(
    report: WikiMeasureReport,
    *,
    out_json: Path,
    out_md: Optional[Path] = None,
) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    if out_md:
        out_md.write_text(render_scorecard_md(report), encoding="utf-8")

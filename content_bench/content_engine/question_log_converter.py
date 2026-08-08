"""Phase-zero question-log → eval-case converter.

Input: a JSONL log of real developer questions with whatever answer or
resolution was recorded (manual-runs.jsonl shape or compatible variants).

Output: eval cases aligned with the specs_to_docs eval_seeds format:
  seed_id, kind, user_query, expected_doc_sections, success_criteria,
  plus pass_criterion and conversion metadata.

Reports how many questions converted cleanly, were ambiguous, or could not
convert (with reasons).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

VALID_VERDICTS = frozenset({"answered_from_docs", "partial", "gap"})


@dataclass
class EvalCase:
    case_id: str
    kind: str
    user_query: str
    expected_doc_sections: List[str] = field(default_factory=list)
    expected_answer: Optional[str] = None
    pass_criterion: str = ""
    success_criteria: List[str] = field(default_factory=list)
    verdict_from_log: str = ""
    source_log: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConversionRow:
    status: str  # converted | ambiguous | failed
    reason: str
    case: Optional[EvalCase] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversionReport:
    input_path: str
    converted_at: str
    rows_total: int
    converted: int
    ambiguous: int
    failed: int
    cases: List[EvalCase] = field(default_factory=list)
    rows: List[ConversionRow] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_path": self.input_path,
            "converted_at": self.converted_at,
            "summary": {
                "rows_total": self.rows_total,
                "converted": self.converted,
                "ambiguous": self.ambiguous,
                "failed": self.failed,
            },
            "cases": [c.to_dict() for c in self.cases],
            "rows": [
                {
                    "status": r.status,
                    "reason": r.reason,
                    "case_id": r.case.case_id if r.case else None,
                    "question": (r.raw.get("question") or r.raw.get("user_query") or "")[:120],
                }
                for r in self.rows
            ],
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slug(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:max_len] or "case").rstrip("-")


def _normalize_sources(raw: Dict[str, Any]) -> List[str]:
    sources: List[str] = []
    for key in ("sources_used", "sources", "expected_doc_sections", "doc_sections"):
        val = raw.get(key)
        if isinstance(val, list):
            sources.extend(str(v).strip() for v in val if str(v).strip())
        elif isinstance(val, str) and val.strip():
            sources.append(val.strip())
    # Dedupe preserving order
    seen: set = set()
    out: List[str] = []
    for s in sources:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _normalize_verdict(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("verdict", "resolution", "outcome", "status"):
        v = raw.get(key)
        if isinstance(v, str):
            v_l = v.strip().lower()
            if v_l in VALID_VERDICTS:
                return v_l
            # Common aliases
            if v_l in ("answered", "pass", "success"):
                return "answered_from_docs"
            if v_l in ("missing", "unknown", "no_docs"):
                return "gap"
    return None


def _normalize_question(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("question", "user_query", "query", "prompt"):
        v = raw.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _normalize_answer(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("answer", "expected_answer", "resolution_text", "notes"):
        v = raw.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _is_ambiguous_question(q: str) -> Optional[str]:
    if len(q) < 12:
        return "question too short to form a pass criterion"
    if q.count("?") == 0 and len(q.split()) < 4:
        return "question lacks interrogative form and is very short"
    if re.match(r"^(yes|no|ok|test)\??$", q.strip(), re.I):
        return "question is not a developer question"
    return None


def _pass_criterion_for(
    verdict: str,
    sources: Sequence[str],
    answer: Optional[str],
    notes: Optional[str],
) -> Tuple[str, List[str]]:
    """Return (pass_criterion, success_criteria)."""
    if verdict == "answered_from_docs":
        crit = "Answer is grounded in the cited doc sections; no facts invented beyond them."
        criteria = [
            "Cites at least one listed doc section",
            "Does not invent endpoints, fields, or auth schemes",
        ]
        if sources:
            criteria.append(f"Primary sources: {', '.join(sources[:5])}")
        return crit, criteria

    if verdict == "partial":
        crit = "Answer acknowledges what the docs cover and explicitly names what is missing."
        criteria = [
            "Names the doc sections that partially apply",
            "States the gap (e.g. missing outcome, sandbox walkthrough, or auth detail)",
        ]
        if notes:
            criteria.append(f"Gap note from log: {notes[:200]}")
        return crit, criteria

    # gap
    crit = "Agent states the published docs do not cover this; does not guess."
    criteria = [
        "Verdict is an honest documentation gap",
        "No invented endpoint paths or field names",
    ]
    if answer:
        criteria.append(f"Log notes: {answer[:200]}")
    return crit, criteria


def _kind_for(verdict: str, question: str) -> str:
    q = question.lower()
    if verdict == "gap":
        return "documentation_gap"
    if verdict == "partial":
        return "partial_coverage"
    if "auth" in q or "401" in q or "signature" in q:
        return "auth_debug"
    if "sandbox" in q or "test" in q:
        return "sandbox_howto"
    if "endpoint" in q or "post " in q or "get " in q:
        return "api_reference"
    return "doc_lookup"


def convert_log_row(raw: Dict[str, Any], *, row_index: int) -> ConversionRow:
    """Convert one log entry to an eval case or report why not."""
    question = _normalize_question(raw)
    if not question:
        return ConversionRow(
            status="failed",
            reason="missing question field (expected question, user_query, or query)",
            raw=raw,
        )

    amb = _is_ambiguous_question(question)
    verdict = _normalize_verdict(raw)
    sources = _normalize_sources(raw)
    answer = _normalize_answer(raw)
    notes = raw.get("notes") if isinstance(raw.get("notes"), str) else None

    if verdict is None:
        if amb:
            return ConversionRow(
                status="ambiguous",
                reason=f"no verdict and {amb}",
                raw=raw,
            )
        return ConversionRow(
            status="failed",
            reason="missing or unknown verdict (expected answered_from_docs, partial, or gap)",
            raw=raw,
        )

    if verdict == "answered_from_docs" and not sources:
        return ConversionRow(
            status="ambiguous",
            reason="answered_from_docs but no sources_used — cannot anchor expected doc section",
            raw=raw,
        )

    if verdict == "gap" and sources:
        return ConversionRow(
            status="ambiguous",
            reason="verdict gap but sources_used is non-empty — conflicting signals",
            raw=raw,
        )

    if amb and verdict != "gap":
        return ConversionRow(
            status="ambiguous",
            reason=amb,
            raw=raw,
        )

    log_id = raw.get("seed_id") or raw.get("id") or raw.get("ts") or str(row_index)
    case_id = raw.get("case_id") or f"manual-{_slug(question)}-{row_index}"

    pass_crit, success = _pass_criterion_for(verdict, sources, answer or notes, notes)

    case = EvalCase(
        case_id=str(case_id),
        kind=_kind_for(verdict, question),
        user_query=question,
        expected_doc_sections=list(sources),
        expected_answer=answer if verdict != "gap" else None,
        pass_criterion=pass_crit,
        success_criteria=success,
        verdict_from_log=verdict,
        source_log={k: v for k, v in raw.items() if k not in ("answer",)},
    )
    return ConversionRow(status="converted", reason="ok", case=case, raw=raw)


def iter_log_rows(path: Path) -> Iterator[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            yield {"_parse_error": str(exc), "_line": line_no, "_raw": line}


def convert_question_log(
    input_path: Path,
    *,
    fail_on_parse_error: bool = False,
) -> ConversionReport:
    rows: List[ConversionRow] = []
    for idx, raw in enumerate(iter_log_rows(input_path)):
        if "_parse_error" in raw:
            row = ConversionRow(
                status="failed",
                reason=f"JSON parse error line {raw.get('_line')}: {raw.get('_parse_error')}",
                raw=raw,
            )
            rows.append(row)
            if fail_on_parse_error:
                continue
            continue
        rows.append(convert_log_row(raw, row_index=idx))

    cases = [r.case for r in rows if r.case is not None]
    return ConversionReport(
        input_path=str(input_path),
        converted_at=_utc_now(),
        rows_total=len(rows),
        converted=sum(1 for r in rows if r.status == "converted"),
        ambiguous=sum(1 for r in rows if r.status == "ambiguous"),
        failed=sum(1 for r in rows if r.status == "failed"),
        cases=cases,
        rows=rows,
    )


def render_conversion_md(report: ConversionReport) -> str:
    s = report.to_dict()["summary"]
    lines = [
        "# Question-log → eval-case conversion report",
        "",
        f"- Input: `{report.input_path}`",
        f"- Converted at: `{report.converted_at}`",
        "",
        "## Summary",
        "",
        f"- Rows total: **{s['rows_total']}**",
        f"- Converted cleanly: **{s['converted']}/{s['rows_total']}**",
        f"- Ambiguous: **{s['ambiguous']}/{s['rows_total']}**",
        f"- Could not convert: **{s['failed']}/{s['rows_total']}**",
        "",
        "## Ambiguous and failed",
        "",
    ]
    for r in report.rows:
        if r.status == "converted":
            continue
        q = (r.raw.get("question") or r.raw.get("user_query") or r.raw.get("_raw") or "")[:80]
        lines.append(f"- **{r.status}**: {r.reason} — `{q}`")

    lines.extend(["", "## Converted cases", ""])
    for c in report.cases:
        lines.append(f"### `{c.case_id}` ({c.kind})")
        lines.append(f"- Question: {c.user_query[:200]}")
        if c.expected_doc_sections:
            lines.append(f"- Expected sections: {', '.join(c.expected_doc_sections)}")
        lines.append(f"- Pass criterion: {c.pass_criterion}")
        lines.append("")

    return "\n".join(lines)


def write_conversion_output(
    report: ConversionReport,
    *,
    out_json: Path,
    out_cases_jsonl: Optional[Path] = None,
    out_md: Optional[Path] = None,
) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")

    if out_cases_jsonl:
        lines = []
        for c in report.cases:
            payload = {
                "stage": "phase_zero_eval_cases",
                "case_id": c.case_id,
                "kind": c.kind,
                "user_query": c.user_query,
                "expected_doc_sections": c.expected_doc_sections,
                "expected_answer": c.expected_answer,
                "pass_criterion": c.pass_criterion,
                "success_criteria": c.success_criteria,
                "verdict_from_log": c.verdict_from_log,
            }
            lines.append(json.dumps(payload))
        out_cases_jsonl.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    if out_md:
        out_md.write_text(render_conversion_md(report), encoding="utf-8")

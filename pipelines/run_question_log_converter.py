#!/usr/bin/env python3
"""Phase-zero question-log → eval-case converter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from content_bench.content_engine.question_log_converter import (  # noqa: E402
    convert_question_log,
    write_conversion_output,
)

DEFAULT_OUT = ROOT / "artifacts" / "content_engine" / "phase_zero" / "question-log-conversion.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a developer question log into eval cases (phase zero)"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="JSONL question log (manual-runs.jsonl shape)",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=DEFAULT_OUT,
        help="Conversion report JSON",
    )
    parser.add_argument(
        "--out-cases",
        type=Path,
        default=None,
        help="Eval cases JSONL output (default: eval-cases.jsonl beside --out-json)",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=None,
        help="Optional markdown summary",
    )
    args = parser.parse_args()

    out_cases = args.out_cases
    if out_cases is None and args.out_json.suffix == ".json":
        out_cases = args.out_json.with_name("eval-cases.jsonl")

    out_md = args.out_md
    if out_md is None and args.out_json.suffix == ".json":
        out_md = args.out_json.with_suffix(".md")

    report = convert_question_log(args.input)
    write_conversion_output(
        report,
        out_json=args.out_json,
        out_cases_jsonl=out_cases,
        out_md=out_md,
    )

    s = report.to_dict()["summary"]
    print(f"[question_log_converter] rows={s['rows_total']} input={args.input}")
    print(
        f"[question_log_converter] converted={s['converted']} "
        f"ambiguous={s['ambiguous']} failed={s['failed']}"
    )
    print(f"[question_log_converter] wrote {args.out_json}")
    if out_cases:
        print(f"[question_log_converter] wrote {out_cases}")
    if out_md:
        print(f"[question_log_converter] wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

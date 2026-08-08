#!/usr/bin/env python3
"""Phase-zero wiki measurement — score an arbitrary markdown wiki folder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from content_bench.content_engine.wiki_measure import (  # noqa: E402
    measure_wiki_folder,
    write_report,
)

DEFAULT_WIKI = ROOT / "content"
DEFAULT_OUT = ROOT / "artifacts" / "content_engine" / "phase_zero" / "wiki-measure.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure wiki/portal markdown quality (phase zero)")
    parser.add_argument(
        "--wiki-root",
        type=Path,
        default=DEFAULT_WIKI,
        help="Folder of markdown pages to score (default: content/)",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=DEFAULT_OUT,
        help="JSON scorecard output path",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=None,
        help="Optional markdown report (default: sibling .md of --out-json)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live-site parity fetch (drift checks n/a)",
    )
    args = parser.parse_args()

    out_md = args.out_md
    if out_md is None and args.out_json.suffix == ".json":
        out_md = args.out_json.with_suffix(".md")

    report = measure_wiki_folder(
        args.wiki_root,
        skip_parity=args.offline,
    )
    write_report(report, out_json=args.out_json, out_md=out_md)

    agg = report.to_dict()["aggregate"]
    print(f"[wiki_measure] pages={agg['pages_total']} wiki_root={args.wiki_root}")
    print(
        f"[wiki_measure] outcomes={agg['steps_with_outcome']}/{agg['steps_total']} "
        f"endpoints_rf={agg['endpoints_with_required_fields']}/{agg['endpoints_total']} "
        f"source_pointer={agg['pages_with_source_pointer']}/{agg['pages_total']}"
    )
    print(f"[wiki_measure] wrote {args.out_json}")
    if out_md:
        print(f"[wiki_measure] wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

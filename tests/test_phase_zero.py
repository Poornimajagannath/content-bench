"""Phase-zero harness: wiki measurement + question-log converter."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from content_bench.content_engine.question_log_converter import convert_question_log
from content_bench.content_engine.wiki_measure import (
    extract_source_pointers,
    measure_endpoints,
    measure_steps,
    measure_wiki_folder,
    parity_drift_checks,
)

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
FIXTURES = ROOT / "tests" / "fixtures" / "phase_zero"
SYNTH_WIKI = FIXTURES / "synthetic_wiki"
SYNTH_LOG = FIXTURES / "synthetic_question_log.jsonl"


def _mock_fetch(url: str) -> tuple[int, str]:
    if "docs.example.com/onboarding" in url:
        return 200, (
            "Create account POST /v1/accounts /v1/account_links "
            "Response includes id starting with acct_ "
            "single-use url account.updated charges_enabled"
        )
    if "docs.example.com/payments/create" in url:
        return 200, (
            "POST /pts/v2/payments clientReferenceInformation "
            "orderInformation.amountDetails.totalAmount currency"
        )
    return 404, "not found"


class WikiMeasureSyntheticTests(unittest.TestCase):
    def test_quickstart_steps_all_have_outcomes(self) -> None:
        text = (SYNTH_WIKI / "quickstart-with-outcomes.md").read_text(encoding="utf-8")
        steps = measure_steps(text)
        self.assertEqual(len(steps), 4)
        self.assertEqual(sum(1 for s in steps if s.has_stated_outcome), 4)
        self.assertEqual(steps[0].detection, "expected_outcome_heading")

    def test_workflow_mixed_outcome_flags(self) -> None:
        text = (SYNTH_WIKI / "workflow-mixed-outcomes.md").read_text(encoding="utf-8")
        steps = measure_steps(text)
        self.assertEqual(len(steps), 3)
        self.assertEqual(sum(1 for s in steps if s.has_stated_outcome), 1)
        flags = [s.detection for s in steps]
        self.assertIn("explicit_flag", flags)

    def test_api_reference_required_fields(self) -> None:
        text = (SYNTH_WIKI / "api-reference-mixed-rf.md").read_text(encoding="utf-8")
        eps = measure_endpoints(text, rel_path="api-reference-mixed-rf.md")
        self.assertEqual(len(eps), 2)
        with_rf = [e for e in eps if e.has_required_fields]
        without_rf = [e for e in eps if not e.has_required_fields]
        self.assertEqual(len(with_rf), 1)
        self.assertEqual(len(without_rf), 1)
        self.assertEqual(with_rf[0].path, "/boarding/v1/registrations")

    def test_a2_reference_table_rf(self) -> None:
        text = (SYNTH_WIKI / "a2-reference-with-rf.md").read_text(encoding="utf-8")
        eps = measure_endpoints(text, rel_path="a2-reference-with-rf.md")
        self.assertEqual(len(eps), 1)
        self.assertTrue(eps[0].has_required_fields)
        self.assertEqual(eps[0].detection, "a2_reference")

    def test_source_pointer_extraction(self) -> None:
        qs = (SYNTH_WIKI / "quickstart-with-outcomes.md").read_text(encoding="utf-8")
        self.assertIn("https://docs.example.com/onboarding", extract_source_pointers(qs))
        orphan = (SYNTH_WIKI / "no-source-pointer.md").read_text(encoding="utf-8")
        self.assertEqual(extract_source_pointers(orphan), [])

    def test_parity_drift_with_mock_fetch(self) -> None:
        text = (SYNTH_WIKI / "quickstart-with-outcomes.md").read_text(encoding="utf-8")
        checks, score = parity_drift_checks(
            text,
            source_urls=["https://docs.example.com/onboarding"],
            fetch_fn=_mock_fetch,
        )
        graded = [c for c in checks if c.result in ("pass", "fail")]
        self.assertGreater(len(graded), 0)
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 30.0)

    def test_synthetic_wiki_aggregate(self) -> None:
        report = measure_wiki_folder(
            SYNTH_WIKI,
            fetch_fn=_mock_fetch,
            exclude_readme=False,
        )
        self.assertEqual(report.pages_total, 5)
        self.assertEqual(report.steps_total, 7)  # 4 quickstart + 3 workflow
        self.assertEqual(report.steps_with_outcome, 5)  # 4 + 1 workflow
        self.assertEqual(report.endpoints_total, 7)  # api-ref 2 + a2 1 + inline across pages
        self.assertEqual(report.pages_with_source_pointer, 3)  # frontmatter + api-fields links
        self.assertEqual(report.pages_without_source_pointer, 2)


class WikiMeasureContentStandInTests(unittest.TestCase):
    def test_content_folder_offline_baseline(self) -> None:
        if not CONTENT.is_dir():
            self.skipTest("content/ not present")
        report = measure_wiki_folder(CONTENT, skip_parity=True)
        self.assertGreater(report.pages_total, 5)
        agg = report.to_dict()["aggregate"]
        self.assertEqual(agg["pages_total"], report.pages_total)
        self.assertEqual(
            agg["steps_with_outcome"] + agg["steps_without_outcome"],
            agg["steps_total"],
        )
        self.assertEqual(
            agg["endpoints_with_required_fields"] + agg["endpoints_without_required_fields"],
            agg["endpoints_total"],
        )
        # connect-quickstart has Expected outcome sections
        qs = next(p for p in report.pages if p.rel_path == "connect-quickstart.md")
        self.assertGreater(qs.steps_total, 0)
        self.assertGreater(qs.steps_with_outcome, 0)
        # A2 payment pages have method/path tables
        cp = next(p for p in report.pages if p.rel_path == "createPayment.md")
        self.assertEqual(cp.endpoints_total, 1)
        self.assertTrue(cp.endpoints_with_required_fields >= 1)


class QuestionLogConverterTests(unittest.TestCase):
    def test_synthetic_log_conversion_counts(self) -> None:
        report = convert_question_log(SYNTH_LOG)
        self.assertEqual(report.rows_total, 6)
        self.assertEqual(report.converted, 3)
        self.assertEqual(report.ambiguous, 1)
        self.assertEqual(report.failed, 2)

    def test_converted_case_shape(self) -> None:
        report = convert_question_log(SYNTH_LOG)
        case = next(c for c in report.cases if "capture" in c.user_query.lower())
        self.assertEqual(case.verdict_from_log, "answered_from_docs")
        self.assertIn("content/capturePayment.md", case.expected_doc_sections)
        self.assertTrue(case.pass_criterion)
        self.assertTrue(case.success_criteria)

    def test_gap_case_no_expected_answer(self) -> None:
        report = convert_question_log(SYNTH_LOG)
        gap = next(c for c in report.cases if c.verdict_from_log == "gap")
        self.assertIsNone(gap.expected_answer)
        self.assertEqual(gap.kind, "documentation_gap")

    def test_report_json_serializable(self) -> None:
        report = convert_question_log(SYNTH_LOG)
        payload = report.to_dict()
        json.dumps(payload)
        self.assertIn("summary", payload)
        self.assertEqual(payload["summary"]["converted"], 3)


if __name__ == "__main__":
    unittest.main()

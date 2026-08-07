"""Extraction recall: constraint prose on short pages; shell triage fields."""

from __future__ import annotations

import unittest

from content_bench.content_engine.ingest import (
    _extract_claims_from_text,
    _first_heading,
    render_ingestion_report,
)


class ExtractionRecallTests(unittest.TestCase):
    def test_ttl_and_reuse_on_short_page(self):
        text = (
            "Processing Authorizations with a Transient Token {#da-payments}\n"
            "==========================================================\n\n"
            "After you validate the transient token, you can use it in place of the "
            "PAN with payment services for 15 minutes. The transient token can be "
            "used multiple times within the 15-minute period.\n"
        )
        claims, drops = _extract_claims_from_text(
            text, source_pointer="da-payments.md", doc_stem="da-payments"
        )
        self.assertFalse(drops)
        blob = " ".join(c.text for c in claims).lower()
        self.assertIn("15 minute", blob)
        self.assertTrue("multiple times" in blob or "reuse" in blob)

    def test_pci_encrypt_header_constraints(self):
        text = (
            "Microform Integration {#mf}\n======================\n\n"
            "You can style these fields to look and behave like any other field on "
            "your website, which could qualify you for PCI DSS SAQ A.\n\n"
            "Sensitive data is encrypted on the customer's device before HTTPS "
            "transmission to Cybersource.\n\n"
            "> IMPORTANT\n"
            "> Each request that you send to Cybersource requires header information.\n"
        )
        claims, drops = _extract_claims_from_text(
            text, source_pointer="mf.md", doc_stem="mf"
        )
        self.assertFalse(drops)
        blob = " ".join(c.text for c in claims).lower()
        self.assertIn("pci", blob)
        self.assertIn("encrypt", blob)
        self.assertIn("header", blob)

    def test_shell_drop_includes_bytes_and_heading(self):
        text = (
            "Introduction to Foo {#foo-intro}\n====================\n\n"
            "See these topics:\n\n* [A](/a.md)\n* [B](/b.md)\n"
        )
        claims, drops = _extract_claims_from_text(
            text, source_pointer="foo-intro.md", doc_stem="foo-intro"
        )
        self.assertEqual(claims, [])
        self.assertEqual(len(drops), 1)
        self.assertEqual(drops[0].reason, "shell")
        self.assertIsNotNone(drops[0].bytes)
        self.assertIn("Introduction to Foo", drops[0].first_heading or "")

    def test_short_constraint_page_is_not_empty_by_length(self):
        text = (
            "Transient tokens {#tt}\n=================\n\n"
            "The transient token is valid for 15 minutes and may be reused within that window.\n"
        )
        claims, drops = _extract_claims_from_text(
            text, source_pointer="tt.md", doc_stem="tt"
        )
        self.assertFalse(drops)
        self.assertGreaterEqual(len(claims), 1)
        self.assertEqual(_first_heading(text), "Transient tokens")

    def test_report_lists_shell_triage_columns_and_sample(self):
        report = {
            "stamp_date": "x",
            "docs_fetched": 1,
            "claims_extracted": 0,
            "claims_by_schema": {},
            "drop_count": 1,
            "drops": [
                {
                    "path": "a.md",
                    "reason": "shell",
                    "detail": "triage",
                    "bytes": 120,
                    "first_heading": "Intro",
                }
            ],
            "raw_dir": "raw/x",
            "normalized_file": "normalized/x.claims.json",
            "read_contract": ["normalized/", "content/"],
            "forbidden_reads": ["raw/"],
            "human_check_sample": [
                {
                    "path": "a.md",
                    "reason": "shell",
                    "bytes": 120,
                    "first_heading": "Intro",
                }
            ],
        }
        md = render_ingestion_report(report)
        self.assertIn("First heading", md)
        self.assertIn("Sampled human check", md)
        self.assertIn("120", md)


if __name__ == "__main__":
    unittest.main()

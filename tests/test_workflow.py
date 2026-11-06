import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from examples.create_demo import create
from seo_system.core import WorkflowError, analyze, database, execute, intake, qa, read_table, resolve, inspect_import

CLOCK = datetime(2026, 11, 6, 18, tzinfo=timezone.utc)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile, self.manifest = create(self.root / "input", CLOCK.isoformat())
        self.workspace = self.root / "workspace"

    def update(self, path, **changes):
        value = json.loads(path.read_text())
        value.update(changes)
        path.write_text(json.dumps(value))

    def pages(self, pages):
        raw = json.dumps(pages).encode()
        (self.manifest.parent / "pages.json").write_bytes(raw)
        self.update(self.manifest, sha256=hashlib.sha256(raw).hexdigest(), row_count=len(pages))

    def run_workflow(self, workflow="technical"):
        return execute(self.profile, self.manifest, self.workspace, workflow, CLOCK)

    def test_end_to_end_trace_and_roadmap(self):
        result = self.run_workflow()
        self.assertEqual(result["status"], "partial")
        path = Path(result["path"])
        findings = json.loads((path / "findings/technical.json").read_text())
        tasks = json.loads((path / "deliverables/tasks.json").read_text())
        self.assertEqual(len(findings), 3)
        self.assertEqual(tasks[0]["priority"], "P1")
        qa(findings, tasks, json.loads((path / "normalized/pages.json").read_text()), findings[0]["evidence"]["artifact_id"])
        self.assertIn("не внедрено", (path / "deliverables/roadmap.md").read_text())
        self.assertEqual(len(list(path.rglob("*.md"))), 3)

    def test_idempotent_resume_after_restart(self):
        first = self.run_workflow()
        second = self.run_workflow()
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertTrue(second["reused"])
        with database(self.workspace) as con:
            self.assertEqual(con.execute("SELECT count(*) FROM runs").fetchone()[0], 1)

    def test_source_mutation_blocks_reuse(self):
        self.run_workflow()
        (self.manifest.parent / "pages.json").write_text("[]")
        with self.assertRaisesRegex(WorkflowError, "checksum"):
            self.run_workflow()

    def test_registered_artifact_mutation_blocks_reuse(self):
        result = self.run_workflow()
        (Path(result["path"]) / "deliverables/report.md").write_text("changed")
        with self.assertRaisesRegex(WorkflowError, "checksum changed"):
            self.run_workflow()

    def test_cross_project_manifest(self):
        self.update(self.manifest, project_id="someone-else")
        with self.assertRaisesRegex(WorkflowError, "different project"):
            self.run_workflow()

    def test_cross_project_registry(self):
        result = self.run_workflow()
        aid = json.loads((Path(result["path"]) / "artifacts.json").read_text())[0]["artifact_id"]
        with database(self.workspace) as con:
            with self.assertRaisesRegex(WorkflowError, "not found"):
                resolve(con, "other-project", result["run_id"], aid, self.workspace)

    def test_wrong_host_rejected(self):
        self.pages([{"url": "https://other.com/", "status_code": 200}])
        with self.assertRaisesRegex(WorkflowError, "scope"):
            self.run_workflow()

    def test_stale_original_timestamp_not_download_time(self):
        self.update(self.manifest, source_generated_at="2026-10-01T18:00:00Z")
        with self.assertRaisesRegex(WorkflowError, "stale"):
            self.run_workflow()

    def test_future_timestamp(self):
        self.update(self.manifest, collected_at="2027-01-01T00:00:00Z")
        with self.assertRaisesRegex(WorkflowError, "future"):
            self.run_workflow()

    def test_revision_invalidates_data(self):
        self.update(self.profile, site_revision="release-2")
        with self.assertRaisesRegex(WorkflowError, "revision"):
            self.run_workflow()

    def test_missing_field_is_not_missing_tag(self):
        self.pages([{"url": "https://example.com/", "status_code": 200}])
        result = self.run_workflow()
        self.assertEqual(json.loads((Path(result["path"]) / "findings/technical.json").read_text()), [])
        self.assertIn("отсутствует у 1 URL", (Path(result["path"]) / "deliverables/coverage.json").read_text())

    def test_no_coercion_of_json_status(self):
        self.pages([{"url": "https://example.com/", "status_code": "200"}])
        with self.assertRaisesRegex(WorkflowError, "integer"):
            self.run_workflow()

    def test_duplicate_urls_rejected(self):
        self.pages([{"url": "https://example.com/", "status_code": 200}] * 2)
        with self.assertRaisesRegex(WorkflowError, "Duplicate"):
            self.run_workflow()

    def test_row_count_mismatch(self):
        self.update(self.manifest, row_count=99)
        with self.assertRaisesRegex(WorkflowError, "row_count"):
            self.run_workflow()

    def test_csv_explicit_mapping(self):
        rows = read_table('Адрес;Код;Заголовок\nhttps://example.com/;200;\n'.encode(),
                          {"format": "csv", "delimiter": ";", "column_mapping": {"url": "Адрес", "status_code": "Код", "title": "Заголовок"}})
        self.assertEqual(rows[0]["title"], "")
        self.assertEqual(rows[0]["status_code"], 200)

    def test_csv_without_mapping_rejected(self):
        with self.assertRaisesRegex(WorkflowError, "column_mapping"):
            read_table(b"url,status_code\nhttps://example.com/,200\n", {"format": "csv"})

    def test_xlsx_explicit_sheet_and_mapping(self):
        from openpyxl import Workbook
        book = Workbook()
        book.active.title = "Страницы"
        book.active.append(["URL", "HTTP"])
        book.active.append(["https://example.com/", 200])
        stream = io.BytesIO()
        book.save(stream)
        rows = read_table(stream.getvalue(), {"format": "xlsx", "sheet": "Страницы", "column_mapping": {"url": "URL", "status_code": "HTTP"}})
        self.assertEqual(rows[0]["status_code"], 200)
        with self.assertRaisesRegex(WorkflowError, "sheet"):
            read_table(stream.getvalue(), {"format": "xlsx", "sheet": "absent"})

    def test_xlsx_formula_rejected(self):
        from openpyxl import Workbook
        book = Workbook()
        book.active.append(["URL", "HTTP"])
        book.active.append(["=1+1", 200])
        stream = io.BytesIO()
        book.save(stream)
        with self.assertRaisesRegex(WorkflowError, "formulas"):
            read_table(stream.getvalue(), {"format": "xlsx", "sheet": "Sheet", "column_mapping": {"url": "URL", "status_code": "HTTP"}})

    def dimensionless_xlsx(self):
        from openpyxl import Workbook
        book = Workbook()
        book.active.append(["URL", "HTTP"])
        book.active.append(["https://example.com/", 200])
        stream = io.BytesIO()
        book.save(stream)
        output = io.BytesIO()
        with zipfile.ZipFile(stream) as original, zipfile.ZipFile(output, "w") as target:
            for entry in original.infolist():
                data = original.read(entry.filename)
                if entry.filename == "xl/worksheets/sheet1.xml":
                    data = re.sub(rb'<dimension[^>]*/>', b'', data)
                target.writestr(entry, data)
        return output.getvalue()

    def test_google_style_xlsx_without_dimensions(self):
        raw = self.dimensionless_xlsx()
        path = self.root / "source.xlsx"
        path.write_bytes(raw)
        inspection = inspect_import(path, "xlsx", "Sheet")
        self.assertIsNone(inspection["sheets"][0]["declared_rows"])
        self.assertEqual(inspection["audit_status"], "not_started")
        self.assertEqual(read_table(raw, {"format": "xlsx", "sheet": "Sheet", "column_mapping": {"url": "URL", "status_code": "HTTP"}}),
                         [{"url": "https://example.com/", "status_code": 200}])

    def test_dimensionless_xlsx_still_enforces_row_limit(self):
        from unittest.mock import patch
        with patch("seo_system.core.MAX_ROWS", 0):
            with self.assertRaisesRegex(WorkflowError, "dimensions exceed"):
                read_table(self.dimensionless_xlsx(), {"format": "xlsx", "sheet": "Sheet", "column_mapping": {"url": "URL", "status_code": "HTTP"}})

    def test_dimensionless_xlsx_end_to_end(self):
        raw = self.dimensionless_xlsx()
        (self.manifest.parent / "pages.xlsx").write_bytes(raw)
        self.update(self.manifest, file="pages.xlsx", format="xlsx", sheet="Sheet", row_count=1,
                    sha256=hashlib.sha256(raw).hexdigest(), column_mapping={"url": "URL", "status_code": "HTTP"})
        result = self.run_workflow()
        self.assertEqual(json.loads((Path(result["path"]) / "normalized/pages.json").read_text()),
                         [{"url": "https://example.com/", "status_code": 200}])

    def test_non_pages_sheet_does_not_become_audit(self):
        from openpyxl import Workbook
        book = Workbook()
        book.active.append(["Task", "Owner"])
        book.active.append(["Review existing reports", "SEO"])
        stream = io.BytesIO()
        book.save(stream)
        with self.assertRaisesRegex(WorkflowError, "Mapped source columns"):
            read_table(stream.getvalue(), {"format": "xlsx", "sheet": "Sheet", "column_mapping": {"url": "URL", "status_code": "HTTP"}})

    def test_qa_fabricated_evidence_blocks(self):
        pages = [{"url": "https://example.com/", "status_code": 503}]
        findings = analyze(pages, "raw-id")
        findings[0]["fact"]["status_code"] = 404
        with self.assertRaisesRegex(WorkflowError, "contradicts"):
            qa(findings, [], pages, "raw-id")

    def test_go_is_partial_and_includes_all_deliverables(self):
        result = self.run_workflow("go")
        self.assertEqual(result["status"], "partial")
        self.assertTrue((Path(result["path"]) / "deliverables/roadmap.md").is_file())

    def test_unknown_workflow_not_claimed(self):
        with self.assertRaisesRegex(WorkflowError, "Unsupported"):
            self.run_workflow("measurement")

    def test_unregistered_directory_is_not_overwritten(self):
        result = self.run_workflow()
        with database(self.workspace) as con:
            con.execute("DELETE FROM tasks")
            con.execute("DELETE FROM artifacts")
            con.execute("DELETE FROM runs")
            con.commit()
        with self.assertRaisesRegex(WorkflowError, "Unregistered"):
            self.run_workflow()
        self.assertTrue(Path(result["path"]).is_dir())

    def test_cli_plan_and_preflight(self):
        for args in [["plan"], ["preflight", "--profile", str(self.profile)]]:
            result = subprocess.run([sys.executable, "-m", "seo_system", *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIsInstance(json.loads(result.stdout), dict)


if __name__ == "__main__":
    unittest.main()

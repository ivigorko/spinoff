"""Validated imports, deterministic findings, and a transactional artifact registry."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import uuid
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 100000


class WorkflowError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def parse_json(raw):
    def invalid(value):
        raise WorkflowError('Non-finite JSON number: ' + value)
    return json.loads(raw, parse_constant=invalid)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc)


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise WorkflowError("Timestamp must include timezone")
    return result.astimezone(timezone.utc)


def validate(kind, value):
    schema = json.loads(files("seo_system").joinpath(f"schemas/{kind}.json").read_text())
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
                    key=lambda e: str(list(e.path)))
    if errors:
        e = errors[0]
        raise WorkflowError(f"{kind}: {list(e.path)}: {e.message}")


def read_json(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise WorkflowError("Input exceeds 20 MiB")
    return parse_json(path.read_text(encoding="utf-8"))


def config(name):
    return json.loads(files("seo_system").joinpath(f"config/{name}.json").read_text())


def check_project(profile):
    validate("project", profile)
    for host in profile["allowed_hosts"]:
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host) or ".." in host:
            raise WorkflowError("Use lowercase ASCII hostnames without schemes or paths")
    if not set(profile["domains"]).issubset(profile["allowed_hosts"]):
        raise WorkflowError("Every domain must be in allowed_hosts")


def check_url(url, hosts):
    parsed = urlsplit(url)
    if (parsed.scheme not in {"http", "https"} or parsed.hostname not in hosts
            or parsed.username or parsed.password or parsed.port not in {None, 80, 443}):
        raise WorkflowError("Page URL is outside project scope")


def read_table(raw, manifest):
    fmt = manifest["format"]
    if fmt == "json":
        return parse_json(raw.decode("utf-8"))
    if fmt == "csv":
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter=manifest.get("delimiter", ","))
        headers = reader.fieldnames
        if not headers or len(set(headers)) != len(headers):
            raise WorkflowError("Missing or duplicate CSV headers")
        rows = list(reader)
        if any(None in r or None in r.values() for r in rows):
            raise WorkflowError("CSV row has inconsistent width")
    else:
        from openpyxl import load_workbook
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if sum(i.file_size for i in archive.infolist()) > 100 * 1024 * 1024:
                raise WorkflowError("XLSX expands beyond 100 MiB")
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=False, keep_links=False)
        try:
            if manifest.get("sheet") not in workbook.sheetnames:
                raise WorkflowError("Select an existing XLSX sheet explicitly")
            sheet = workbook[manifest["sheet"]]
            # Google Sheets exports may omit worksheet dimension metadata.
            if (sheet.max_row is not None and sheet.max_row > MAX_ROWS + 1) or (sheet.max_column is not None and sheet.max_column > 200):
                raise WorkflowError("XLSX dimensions exceed limits")
            values = sheet.iter_rows()
            header_cells = next(values, None)
            if header_cells is None:
                raise WorkflowError("Empty XLSX sheet")
            headers = [cell.value for cell in header_cells]
            if len(headers) > 200:
                raise WorkflowError("XLSX dimensions exceed limits")
            if not all(isinstance(h, str) for h in headers) or len(set(headers)) != len(headers):
                raise WorkflowError("Missing or duplicate XLSX headers")
            rows = []
            for row_number, cells in enumerate(values, start=2):
                if row_number > MAX_ROWS + 1 or len(cells) > 200:
                    raise WorkflowError("XLSX dimensions exceed limits")
                if any(c.data_type == "f" for c in cells):
                    raise WorkflowError("XLSX formulas are not accepted")
                row = dict(zip(headers, [c.value for c in cells]))
                if any(v is not None for v in row.values()):
                    rows.append(row)
        finally:
            workbook.close()
    mapping = manifest.get("column_mapping")
    if not mapping or "url" not in mapping or "status_code" not in mapping:
        raise WorkflowError("CSV/XLSX requires explicit column_mapping including url and status_code")
    if not set(mapping.values()).issubset(headers):
        raise WorkflowError("Mapped source columns do not exist")
    result = []
    for row in rows:
        page = {}
        for target, source in mapping.items():
            value = row[source]
            if value is None or value == "":
                if target in {"url", "status_code"}:
                    raise WorkflowError("Missing mandatory value")
                value = "" if target in {"title", "h1"} else None
            if target == "status_code" and isinstance(value, str):
                if not re.fullmatch(r"[1-5][0-9]{2}", value):
                    raise WorkflowError("Invalid HTTP status code")
                value = int(value)
            if value is not None:
                page[target] = value
        result.append(page)
    return result


def inspect_import(path, fmt, sheet_name=None):
    """Inspect a bounded local container, without treating it as measured pages."""
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise WorkflowError("Source exceeds 20 MiB")
    raw = path.read_bytes()
    result = {"format": fmt, "bytes": len(raw), "sha256": digest(raw),
              "source_access": "local_file_only", "audit_status": "not_started"}
    if fmt == "xlsx":
        from openpyxl import load_workbook
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if sum(i.file_size for i in archive.infolist()) > 100 * 1024 * 1024:
                raise WorkflowError("XLSX expands beyond 100 MiB")
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=False, keep_links=False)
        try:
            result["sheets"] = [{"name": s.title, "declared_rows": s.max_row,
                                  "declared_columns": s.max_column} for s in workbook]
            if sheet_name is not None:
                if sheet_name not in workbook.sheetnames:
                    raise WorkflowError("Select an existing XLSX sheet explicitly")
                cells = next(workbook[sheet_name].iter_rows(), [])
                if len(cells) > 200:
                    raise WorkflowError("XLSX dimensions exceed limits")
                if any(c.data_type == "f" for c in cells):
                    raise WorkflowError("XLSX header formulas are not accepted")
                result["first_row"] = [c.value if isinstance(c.value, (str, int, float, bool, type(None))) else str(c.value) for c in cells]
        finally:
            workbook.close()
    elif fmt == "csv":
        # This is an inspection preview; normalization still requires explicit delimiter/mapping.
        result["first_line"] = raw.decode("utf-8-sig").splitlines()[0] if raw else ""
        result["delimiter_status"] = "select_explicitly_in_manifest"
    else:
        value = json.loads(raw.decode("utf-8"))
        result["json_type"] = type(value).__name__
        result["row_count"] = len(value) if isinstance(value, list) else None
    result["note"] = "Container inspection only: verify report kind, mapping, source date, scope and provenance before import"
    return result


def intake(profile_path, manifest_path, clock=None):
    profile, manifest = read_json(profile_path), read_json(manifest_path)
    check_project(profile)
    validate("source-manifest", manifest)
    if manifest["project_id"] != profile["project_id"]:
        raise WorkflowError("Manifest belongs to a different project")
    if manifest["host"] not in profile["allowed_hosts"]:
        raise WorkflowError("Manifest host is outside allowed_hosts")
    current = clock or now()
    generated, collected = timestamp(manifest["source_generated_at"]), timestamp(manifest["collected_at"])
    if generated > collected or collected > current:
        raise WorkflowError("Source chronology is invalid or in the future")
    if (current - generated).total_seconds() > config("freshness")["pages"] * 86400:
        raise WorkflowError("Pages source is stale; downloading again does not refresh source time")
    if manifest["site_revision"] != profile["site_revision"]:
        raise WorkflowError("Site revision changed; obtain a fresh source")
    source = (Path(manifest_path).resolve().parent / manifest["file"]).resolve()
    if source.stat().st_size > MAX_BYTES:
        raise WorkflowError("Source exceeds 20 MiB")
    raw = source.read_bytes()
    if digest(raw) != manifest["sha256"]:
        raise WorkflowError("Source checksum mismatch")
    pages = read_table(raw, manifest)
    validate("pages", pages)
    if len(pages) != manifest["row_count"]:
        raise WorkflowError("Manifest row_count mismatch")
    seen = set()
    for page in pages:
        check_url(page["url"], profile["allowed_hosts"])
        if urlsplit(page["url"]).hostname != manifest["host"]:
            raise WorkflowError("Page host differs from manifest host; split host scopes")
        if page["url"] in seen:
            raise WorkflowError("Duplicate page URL")
        seen.add(page["url"])
    return profile, manifest, raw, pages


def analyze(pages, raw_id):
    findings = []
    for i, page in enumerate(pages):
        checks = []
        status = page["status_code"]
        if status >= 400:
            checks.append(("http_error", "high", "status_code", "Проверить назначение URL и восстановить доступность либо исправить ссылки на него", "Повторный HTTP-запрос: URL соответствует согласованному назначению; внутренние ссылки не ведут на ошибку"))
        if status == 200 and page.get("title") == "":
            checks.append(("missing_title", "medium", "title", "Подготовить уникальный title по содержанию страницы и согласованному интенту", "В новом HTML один непустой title соответствует согласованному тексту"))
        if status == 200 and page.get("h1") == "":
            checks.append(("missing_h1", "medium", "h1", "Подготовить основной заголовок по назначению страницы", "В новом HTML присутствует согласованный основной H1"))
        for code, severity, field, action, acceptance in checks:
            f = {"finding_id": "f-" + digest((page["url"] + code).encode())[:16],
                 "category": "technical", "code": code, "severity": severity,
                 "url": page["url"], "fact": {field: page[field]},
                 "evidence": {"artifact_id": raw_id, "row_index": i, "field": field},
                 "action": action, "acceptance_test": acceptance,
                 "expected_effect": "Гипотеза: устранение технической проблемы улучшит доступность или представление страницы; рост не гарантирован"}
            validate("finding", f)
            findings.append(f)
    return sorted(findings, key=lambda f: ({"high": 0, "medium": 1}[f["severity"]], f["finding_id"]))


def prioritize(findings):
    tasks = []
    for finding in findings:
        task = {"task_id": "task-" + finding["finding_id"], "finding_ids": [finding["finding_id"]],
                "url": finding["url"], "action": finding["action"], "owner_role": "developer" if finding["code"] == "http_error" else "seo_editor",
                "priority": "P1" if finding["severity"] == "high" else "P2",
                "effort_hours": None, "dependencies": [], "risk": "Нужны проверка назначения URL и ревью перед изменением",
                "acceptance_test": finding["acceptance_test"], "metric": "Техническая проверка URL; SEO-эффект измеряется отдельно",
                "measurement_window": "После релиза: новая техническая проверка; аналитическое окно согласовать по baseline",
                "required_permission": "apply/publish according to actual user authorization", "expected_effect": finding["expected_effect"]}
        validate("task", task)
        tasks.append(task)
    return tasks


def qa(findings, tasks, pages, raw_id):
    for finding in findings:
        validate("finding", finding)
        ev = finding["evidence"]
        if ev["artifact_id"] != raw_id or ev["row_index"] >= len(pages):
            raise WorkflowError("Finding evidence does not resolve")
        page = pages[ev["row_index"]]
        if page["url"] != finding["url"] or finding["fact"] != {ev["field"]: page.get(ev["field"])}:
            raise WorkflowError("Finding contradicts evidence")
    ids = {f["finding_id"] for f in findings}
    if len(ids) != len(findings) or {f for t in tasks for f in t["finding_ids"]} != ids:
        raise WorkflowError("Roadmap does not cover every finding exactly by reference")
    for task in tasks:
        validate("task", task)
        if not set(task["finding_ids"]).issubset(ids):
            raise WorkflowError("Task references unknown finding")


def markdown(value):
    # Source text cannot inject report HTML, headings or table rows.
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("\n", " ").replace("\r", " ").replace("`", "&#96;")


def render(profile, manifest, findings, tasks, coverage):
    report = [f"# Технический отчёт — {markdown(profile['project_id'])}",
              "", "Статус: partial. Проверены только данные импортированной выборки; live-проверка не выполнялась.",
              f"Источник: {markdown(manifest['source_id'])}; locator: {markdown(manifest['source_locator'])}.",
              f"Дата исходного сбора: {manifest['source_generated_at']}. Строк: {manifest['row_count']}.",
              "", "## Покрытие", "", *[f"- {markdown(x)}" for x in coverage["limitations"]],
              "", "## Находки", ""]
    if not findings:
        report.append("Проблем по выполненным правилам в выборке не найдено. Это не подтверждает исправность сайта в целом.")
    for f in findings:
        report.extend([f"- {f['finding_id']} / {f['severity']}: {markdown(f['url'])} — {f['code']}; факт: {markdown(canonical(f['fact']))}; evidence: {f['evidence']['artifact_id']} row_index={f['evidence']['row_index']} field={f['evidence']['field']}."])
    priority = ["# Приоритеты", "", "Порядок: HTTP-ошибки → отсутствующие элементы. Бизнес-эффект и трудозатраты ещё не оценены.", ""]
    roadmap = ["# Roadmap", "", "Мощность команды неизвестна; это последовательность и сценарий 30/60/90 дней, без обещанного календаря.",
               "", "1. До 30 дней при наличии ресурсов: согласовать назначение URL и подготовить задачи ниже; проверить baseline и выбрать первую правку.",
               "2. 31–60 дней: после приёмки предыдущих задач внедрять согласованные исправления, проверять фактические URL после каждого релиза.",
               "3. 61–90 дней: при наступлении согласованного окна сравнить сопоставимые периоды, учесть сезонность и другие изменения; уточнить backlog.",
               "", "Ничего не внедрено. Публикация: not_requested. Проверка production: not_started. Измерение: awaiting_baseline.", ""]
    for task in tasks:
        priority.append(f"- {task['priority']} / {task['task_id']}: {markdown(task['url'])}; {task['action']}")
        roadmap.extend([f"## {task['task_id']}", "", f"URL: {markdown(task['url'])}; finding: {', '.join(task['finding_ids'])}.",
                        f"Действие: {task['action']}", f"Роль: {task['owner_role']}; усилия: неизвестны; зависимости: согласование назначения и baseline.",
                        f"Риск: {task['risk']}", f"Приёмка: {task['acceptance_test']}", f"Эффект: {task['expected_effect']}",
                        f"Метрика и окно: {task['metric']}; {task['measurement_window']}", f"Полномочия: {task['required_permission']}", ""])
    return {"report.md": "\n".join(report), "priority.md": "\n".join(priority), "roadmap.md": "\n".join(roadmap)}


DDL = """
CREATE TABLE IF NOT EXISTS runs(
 project_id TEXT NOT NULL, run_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
 status TEXT NOT NULL, created_at TEXT NOT NULL, output_path TEXT NOT NULL,
 PRIMARY KEY(project_id, run_id), UNIQUE(project_id, fingerprint));
CREATE TABLE IF NOT EXISTS artifacts(
 project_id TEXT NOT NULL, run_id TEXT NOT NULL, artifact_id TEXT NOT NULL,
 metadata TEXT NOT NULL, PRIMARY KEY(project_id,run_id,artifact_id),
 FOREIGN KEY(project_id,run_id) REFERENCES runs(project_id,run_id));
CREATE TABLE IF NOT EXISTS tasks(
 project_id TEXT NOT NULL, run_id TEXT NOT NULL, node_id TEXT NOT NULL,
 status TEXT NOT NULL, dependencies TEXT NOT NULL,
 PRIMARY KEY(project_id,run_id,node_id),
 FOREIGN KEY(project_id,run_id) REFERENCES runs(project_id,run_id));
CREATE TABLE IF NOT EXISTS events(
 project_id TEXT NOT NULL, run_id TEXT NOT NULL, at TEXT NOT NULL, event TEXT NOT NULL);
"""


@contextmanager
def database(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    con = sqlite3.connect(root / "state.sqlite3", timeout=1)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(DDL)
    try:
        yield con
    finally:
        con.close()


def resolve(con, project_id, run_id, artifact_id, root):
    row = con.execute("SELECT metadata FROM artifacts WHERE project_id=? AND run_id=? AND artifact_id=?",
                      (project_id, run_id, artifact_id)).fetchone()
    if not row:
        raise WorkflowError("Artifact not found in project/run scope")
    artifact = json.loads(row[0])
    path = (Path(root).resolve() / artifact["logical_path"]).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise WorkflowError("Artifact path escaped workspace")
    if not path.is_file() or digest(path.read_bytes()) != artifact["sha256"]:
        raise WorkflowError("Registered artifact missing or checksum changed")
    return path


def execute(profile_path, manifest_path, root, workflow="technical", clock=None):
    if workflow not in config("workflows"):
        raise WorkflowError("Unsupported executable workflow")
    profile, manifest, raw, pages = intake(profile_path, manifest_path, clock)
    root = Path(root).resolve()
    project_id = profile["project_id"]
    # Implementation and policy identity invalidate cache when either changes.
    implementation = digest(Path(__file__).read_bytes())
    schemas_hash = digest(b"".join(p.read_bytes() for p in sorted(files("seo_system").joinpath("schemas").iterdir(), key=str)))
    fingerprint = digest(canonical([profile, manifest, workflow, config("freshness"), config("workflows"), implementation, schemas_hash]).encode())
    with database(root) as con:
        con.execute("BEGIN IMMEDIATE")  # single writer, held for the entire local operation
        existing = con.execute("SELECT run_id,output_path FROM runs WHERE project_id=? AND fingerprint=?",
                               (project_id, fingerprint)).fetchone()
        if existing:
            for (aid,) in con.execute("SELECT artifact_id FROM artifacts WHERE project_id=? AND run_id=?", (project_id, existing[0])):
                resolve(con, project_id, existing[0], aid, root)
            return {"project_id": project_id, "run_id": existing[0], "path": existing[1], "status": "partial", "reused": True}
        run_id = "run-" + fingerprint[:20]
        relative = Path("projects") / project_id / "runs" / run_id
        destination = root / relative
        if destination.exists():
            raise WorkflowError("Unregistered run directory exists after an interrupted write; see docs/recovery.md")
        staging = root / (".staging-" + uuid.uuid4().hex)
        staging.mkdir(mode=0o700)
        created_at = (clock or now()).isoformat()
        try:
            raw_id = "raw-" + manifest["sha256"][:20]
            findings = analyze(pages, raw_id)
            tasks = prioritize(findings)
            qa(findings, tasks, pages, raw_id)
            limitations = ["Проверены только HTTP-статусы и наличие title/H1 при доступности соответствующих полей.",
                           "Индексация, robots, sitemap, canonical, CWV, семантика, конкуренты, ссылки, AI-видимость и аналитика не проверены.",
                           "Drive storage adapter не реализован: результаты сохранены только локально."]
            if not manifest["coverage"]["complete"]:
                limitations.append("Выборка неполная: " + manifest["coverage"]["reason"])
            for field in ["title", "h1"]:
                missing = sum(field not in p for p in pages)
                if missing:
                    limitations.append(f"Поле {field} отсутствует у {missing} URL; соответствующая проверка пропущена.")
            coverage = {"status": "partial", "rows": len(pages), "limitations": limitations,
                        "source_coverage": manifest["coverage"], "workflow": workflow}
            outputs = {"raw/source." + manifest["format"]: raw,
                       "normalized/pages.json": canonical(pages).encode(),
                       "findings/technical.json": canonical(findings).encode(),
                       "deliverables/tasks.json": canonical(tasks).encode(),
                       "deliverables/coverage.json": canonical(coverage).encode(),
                       "deliverables/qa.json": canonical({"critical_checks": "pass", "analysis_status": "partial", "publication_status": "not_requested", "verification_status": "not_started", "measurement_status": "awaiting_baseline"}).encode(),
                       "manifest.json": canonical({"profile": profile, "source_manifest": manifest, "fingerprint": fingerprint, "implementation_sha256": implementation, "schemas_sha256": schemas_hash}).encode()}
            outputs.update({"deliverables/" + name: text.encode() for name, text in render(profile, manifest, findings, tasks, coverage).items()})
            artifacts = []
            for name, data in outputs.items():
                path = staging / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                aid = raw_id if name.startswith("raw/") else "art-" + digest(name.encode())[:20]
                artifact = {"schema_version": 1, "artifact_id": aid, "project_id": project_id, "run_id": run_id,
                            "logical_path": str(relative / name), "kind": name, "sha256": digest(data),
                            "created_at": created_at, "status": "local_validated", "storage": {"provider": "local"},
                            "parent_artifact_ids": [] if aid == raw_id else [raw_id]}
                validate("artifact", artifact)
                artifacts.append(artifact)
            (staging / "artifacts.json").write_text(canonical(artifacts), encoding="utf-8")
            con.execute("INSERT INTO runs VALUES(?,?,?,?,?,?)", (project_id, run_id, fingerprint, "partial", created_at, str(destination)))
            for artifact in artifacts:
                con.execute("INSERT INTO artifacts VALUES(?,?,?,?)", (project_id, run_id, artifact["artifact_id"], canonical(artifact)))
            for node, deps in config("workflows")[workflow].items():
                con.execute("INSERT INTO tasks VALUES(?,?,?,?,?)", (project_id, run_id, node, "succeeded", canonical(deps)))
                con.execute("INSERT INTO events VALUES(?,?,?,?)", (project_id, run_id, created_at, node + ":succeeded"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.rename(staging, destination)
            con.commit()
        finally:
            if staging.exists():
                shutil.rmtree(staging)  # only our own unpublished temporary output
    return {"project_id": project_id, "run_id": run_id, "path": str(destination), "status": "partial", "reused": False}

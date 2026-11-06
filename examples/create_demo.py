"""Generate clearly synthetic offline inputs; never relabel real source dates."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def create(directory, at=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    at = at or datetime.now(timezone.utc).isoformat()
    profile = {"schema_version": 1, "project_id": "synthetic-demo", "profile_version": 1,
               "domains": ["example.com"], "allowed_hosts": ["example.com"], "site_revision": "synthetic-v1",
               "business_goals": ["Демонстрация технического анализа; не клиентский проект"],
               "timezone": "Etc/UTC", "market": {"country": "RU", "region": "demo-only", "language": "ru", "engines": ["yandex", "google"], "devices": ["desktop"]},
               "drive_root_folder_id": None, "monthly_capacity_hours": None}
    pages = [{"url": "https://example.com/", "status_code": 200, "title": "", "h1": "Example"},
             {"url": "https://example.com/service", "status_code": 503},
             {"url": "https://example.com/about", "status_code": 200, "title": "About", "h1": ""}]
    raw = json.dumps(pages, ensure_ascii=False).encode()
    manifest = {"schema_version": 1, "project_id": "synthetic-demo", "source_id": "manual_fixture",
                "source_locator": "synthetic-demo: not a live crawl or Labrika export", "primary_origin": "generated synthetic fixture",
                "kind": "pages", "host": "example.com", "site_revision": "synthetic-v1", "file": "pages.json",
                "format": "json", "sha256": hashlib.sha256(raw).hexdigest(), "row_count": len(pages),
                "collected_at": at, "source_generated_at": at,
                "coverage": {"complete": False, "reason": "Synthetic three-page example; no real website inspected"}}
    (directory / "pages.json").write_bytes(raw)
    for name, value in [("profile", profile), ("source-manifest", manifest)]:
        (directory / (name + ".json")).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return directory / "profile.json", directory / "source-manifest.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(*create(args.output), sep="\n")

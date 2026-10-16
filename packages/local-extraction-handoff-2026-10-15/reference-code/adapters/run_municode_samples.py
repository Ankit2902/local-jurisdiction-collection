"""Run the reusable Municode collector against every reviewed Municode mapping.

This is an implementation-track harness, not the eventual all-provider batch
manager.  It purposefully produces a two-section acceptance sample per source
before a full crawl is authorized.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from adapters.municode_collector import MunicodeCollector, ROOT

REGISTRIES = (ROOT / "data" / "california-validation-registry.json",
              ROOT / "data" / "central-east-validation-registry.json",
              ROOT / "data" / "washington-arizona-validation-registry.json")


def jurisdiction_names() -> dict[str, str]:
    with (ROOT / "data" / "local-jurisdictions.csv").open(encoding="utf-8-sig", newline="") as source:
        return {row["slug"]: row["jurisdiction"] for row in csv.DictReader(source)}


def municode_entries() -> list[dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for path in REGISTRIES:
        registry = json.loads(path.read_text(encoding="utf-8"))
        for slug, entry in registry["jurisdictions"].items():
            if entry.get("adapter") == "municode":
                entries[slug] = {"slug": slug, "root_url": entry["root_url"]}
    return [entries[key] for key in sorted(entries)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Municode acceptance samples")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--slug", action="append", help="restrict to one or more slugs")
    parser.add_argument("--delay", type=float, default=.35)
    args = parser.parse_args()
    names = jurisdiction_names()
    selected = [e for e in municode_entries() if not args.slug or e["slug"] in args.slug]
    failures, completed = [], []
    for entry in selected:
        try:
            manifest = MunicodeCollector(entry["slug"], names[entry["slug"]], entry["root_url"], delay=args.delay).collect(args.limit)
            completed.append({"slug": entry["slug"], "manifest": manifest})
            print("PASS", entry["slug"], manifest["metadata"]["collected_sections"], "sections")
        except Exception as exc:  # retain failures without losing other jurisdictions
            failures.append({"slug": entry["slug"], "error": str(exc)})
            print("FAIL", entry["slug"], exc)
    report = {"adapter": "municode", "sample_limit": args.limit, "completed": completed, "failures": failures}
    report_path = ROOT / "validation" / "full-collectors" / "municode-sample-run.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", report_path)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

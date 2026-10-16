#!/usr/bin/env python3
"""Sequential, resumable manager for reviewed municipal-code collectors.

This is the production entry point.  Explicit ``--slug`` runs resolve only the
selected workbook jurisdictions, while ``--all`` remains fail-closed against
the complete current workbook.  Resolved targets use a completed Municode,
browser-vendor, or first-party/bulk collector; keep a run ledger; and write both
TOC and full-text CSV/JSON artifacts.  Browser vendors are intentionally run one
at a time because the collector uses a visible Chrome session and publishers
should not be hit concurrently.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from adapters.browser_vendor_collectors import (  # noqa: E402
    BrowserVendorCollector,
    ChromeRenderedTransport,
    Publication,
)
from adapters.municode_collector import MunicodeCollector  # noqa: E402
from adapters import special_collectors  # noqa: E402

SCHEMA = [
    "jurisdiction", "code_name", "division", "title", "subtitle", "chapter",
    "subchapter", "article", "part", "subpart", "section_number", "section_name",
    "citation", "full_text", "source_url", "scrape_date",
]
REGISTRIES = (
    ROOT / "data" / "california-validation-registry.json",
    ROOT / "data" / "central-east-validation-registry.json",
    ROOT / "data" / "washington-arizona-validation-registry.json",
)
BROWSER_INDEX = ROOT / "validation" / "collector-completion" / "browser-vendors" / "index.json"
SPECIAL_SLUGS = {
    "new-york-city-ny", "san-mateo-ca", "san-diego-ca", "king-county-wa",
    "portland-me", "rockland-me",
}
DEFAULT_OUTPUT = ROOT / "outputs" / "production"
DEFAULT_STATUS = ROOT / "manager-status"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def workbook_jurisdictions() -> dict[str, dict[str, str]]:
    with (ROOT / "data" / "local-jurisdictions.csv").open(encoding="utf-8-sig", newline="") as handle:
        return {row["slug"]: row for row in csv.DictReader(handle)}


def reviewed_routes() -> dict[str, dict[str, str]]:
    routes: dict[str, dict[str, str]] = {}
    for registry_path in REGISTRIES:
        for slug, entry in read_json(registry_path)["jurisdictions"].items():
            if slug in routes:
                raise RuntimeError(f"Duplicate reviewed route for {slug}")
            routes[slug] = dict(entry)
    return routes


def build_targets(requested: list[str] | None = None, *, all_targets: bool = False) -> list[dict[str, str]]:
    """Resolve reviewed collector routes for an explicit scope.

    A selected run must not be coupled to unrelated workbook entries that are
    still being qualified.  Conversely, an all-portfolio run must resolve every
    current workbook row; no frozen jurisdiction count or readiness bypass is
    accepted.
    """
    jurisdictions, routes = workbook_jurisdictions(), reviewed_routes()
    browser = {record["slug"]: record for record in read_json(BROWSER_INDEX)["records"]}
    if all_targets:
        selected = sorted(jurisdictions)
    else:
        if not requested:
            raise RuntimeError("Select one or more --slug values, or explicitly pass --all")
        unknown = sorted(set(requested) - set(jurisdictions))
        if unknown:
            raise RuntimeError("Unknown jurisdiction slug(s): " + ", ".join(unknown))
        # Preserve CLI order while avoiding duplicate collection in one run.
        selected = list(dict.fromkeys(requested))

    targets: list[dict[str, str]] = []
    unresolved: list[str] = []
    for slug in selected:
        source = jurisdictions[slug]
        route = routes.get(slug)
        if not route:
            unresolved.append(f"{slug}: no reviewed source route")
            continue
        if slug in SPECIAL_SLUGS:
            kind = "special"
        elif route["adapter"] == "municode":
            kind = "municode"
        elif slug in browser:
            kind = "browser"
        else:
            unresolved.append(f"{slug}: no registered full collector")
            continue
        target = {
            "slug": slug,
            "jurisdiction": source["jurisdiction"],
            "entity_type": source["entity_type"],
            "kind": kind,
            "adapter": route["adapter"],
            "root_url": route["root_url"],
        }
        if kind == "browser":
            target["effective_adapter"] = browser[slug].get("live_sample", {}).get(
                "effective_adapter", browser[slug]["collector_adapter"]
            )
        targets.append(target)
    if unresolved:
        scope = "all-portfolio" if all_targets else "selected"
        raise RuntimeError(f"Cannot resolve {scope} target scope: " + "; ".join(unresolved))
    if all_targets and len(targets) != len(jurisdictions):
        raise RuntimeError(
            f"All-portfolio target resolution was incomplete: expected {len(jurisdictions)}, found {len(targets)}"
        )
    return targets


def full_payload(path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    payload = read_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("provisions"), list):
        raise RuntimeError(f"Expected a provision JSON export at {path}")
    rows = payload["provisions"]
    if not rows or any(set(row) != set(SCHEMA) for row in rows):
        raise RuntimeError(f"{path} does not contain non-empty 16-column provision rows")
    return dict(payload.get("metadata") or {}), rows


def write_toc_from_fulltext(full_json: Path, full_csv: Path) -> dict[str, str]:
    """Write a separate TOC artifact without losing the full-text export.

    Some provider APIs naturally return the index and enactment in one call.
    The manager still publishes an explicit TOC companion so every provider has
    the same downstream contract.
    """
    metadata, rows = full_payload(full_json)
    toc_rows = [{field: ("" if field == "full_text" else row.get(field, "")) for field in SCHEMA}
                for row in rows]
    stem = full_json.stem
    toc_stem = stem[:-len("-fulltext")] + "-toc" if stem.endswith("-fulltext") else stem + "-toc"
    toc_json, toc_csv = full_json.with_name(toc_stem + ".json"), full_csv.with_name(toc_stem + ".csv")
    toc_metadata = {**metadata, "artifact": "toc", "total_provisions": len(toc_rows), "full_text_complete": 0}
    atomic_json(toc_json, {"metadata": toc_metadata, "provisions": toc_rows})
    with toc_csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA)
        writer.writeheader(); writer.writerows(toc_rows)
    return {"toc_json": str(toc_json), "toc_csv": str(toc_csv),
            "fulltext_json": str(full_json), "fulltext_csv": str(full_csv), "rows": str(len(rows))}


def normalize_outputs(result: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, str]]:
    values = result if isinstance(result, list) else [result]
    artifacts: list[dict[str, str]] = []
    for item in values:
        json_path, csv_path = Path(item["json"]), Path(item["csv"])
        artifacts.append(write_toc_from_fulltext(json_path, csv_path))
    return artifacts


def write_browser_family_outputs(slug: str, jurisdiction: str, aggregate_json: Path,
                                 output_dir: Path) -> list[dict[str, str]]:
    """Split a browser collector's checkpoint-friendly aggregate by code family."""
    metadata, rows = full_payload(aggregate_json)
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        family = (row.get("code_name") or "Municipal Code").strip()
        groups.setdefault(family, []).append(row)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, str]] = []
    used_keys: set[str] = set()
    for family, family_rows in groups.items():
        short_name = re.sub(rf"^{re.escape(jurisdiction)}\s+", "", family, flags=re.I).strip()
        key = re.sub(r"[^a-z0-9]+", "_", short_name.lower()).strip("_")
        if key in {"municipal_code", "code_of_ordinances"}:
            key = "code"
        if not key or key in used_keys:
            raise RuntimeError(f"Ambiguous browser code-family output key for {slug}: {family!r}")
        used_keys.add(key)
        stem = f"{slug}-municipal-{key}"
        json_path, csv_path = output_dir / f"{stem}.json", output_dir / f"{stem}.csv"
        family_metadata = {**metadata, "code_name": family,
                           "total_provisions": len(family_rows),
                           "full_text_complete": sum(bool(row["full_text"]) for row in family_rows)}
        atomic_json(json_path, {"metadata": family_metadata, "provisions": family_rows})
        with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=SCHEMA)
            writer.writeheader(); writer.writerows(family_rows)
        outputs.append({"json": str(json_path), "csv": str(csv_path)})
    return outputs


def collect_special(target: dict[str, str], work_root: Path) -> dict[str, Any] | list[dict[str, Any]]:
    slug = target["slug"]
    if slug == "new-york-city-ny":
        return special_collectors.collect_nyc_bulk(work_root)
    if slug == "san-mateo-ca":
        return special_collectors.collect_san_mateo_bulk(work_root)
    if slug == "san-diego-ca":
        return special_collectors.collect_san_diego_all(work_root)
    if slug == "king-county-wa":
        return special_collectors.collect_king_county(work_root, target["root_url"])
    if slug == "portland-me":
        return special_collectors.collect_portland_me(work_root, target["root_url"])
    if slug == "rockland-me":
        return special_collectors.collect_rockland_me(work_root, target["root_url"])
    raise RuntimeError(f"No special collector registered for {slug}")


def collect_one(target: dict[str, str], output_root: Path, *, browser_port: int,
                max_pages: int, municode_delay: float) -> dict[str, Any]:
    """Run one full collector and return normalized artifacts for the ledger."""
    work_root = output_root / target["slug"]
    kind = target["kind"]
    if kind == "municode":
        manifest = MunicodeCollector(target["slug"], target["jurisdiction"], target["root_url"],
                                     work_root, delay=municode_delay).collect()
        result: dict[str, Any] | list[dict[str, Any]] = {
            "json": manifest["output_json"], "csv": manifest["output_csv"],
            "rows": manifest["metadata"]["collected_sections"],
            "full_text_rows": manifest["metadata"]["full_text_complete"],
        }
    elif kind == "browser":
        publication = Publication(target["slug"], target["jurisdiction"], target["effective_adapter"],
                                  target["root_url"], max_pages=max_pages)
        transport = ChromeRenderedTransport(work_root / "cache", debug_port=browser_port)
        collector = BrowserVendorCollector(publication, transport, work_root / "checkpoint")
        collector.collect(max_pages=max_pages)
        aggregate = collector.write_outputs(work_root)
        result = write_browser_family_outputs(
            target["slug"], target["jurisdiction"], Path(aggregate["json"]), work_root / "outputs")
    elif kind == "special":
        result = collect_special(target, work_root)
    else:  # pragma: no cover - build_targets constrains this
        raise RuntimeError(f"Unsupported collector kind: {kind}")
    artifacts = normalize_outputs(result)
    return {"artifacts": artifacts, "raw_result": result}


def readiness_check(targets: list[dict[str, str]], *, all_targets: bool) -> dict[str, Any]:
    """Require completion evidence for the exact run scope.

    ``--all`` executes and persists the canonical whole-portfolio audit.  A
    selected run validates the same evidence types for only the requested
    slugs, so unrelated routes under qualification do not block approved work.
    """
    from validation import audit_full_collector_readiness

    if all_targets:
        result = audit_full_collector_readiness.main()
        report = read_json(ROOT / "validation" / "full-collectors" / "readiness-audit.json")
    else:
        result = 0
        report = audit_full_collector_readiness.audit({target["slug"] for target in targets})
    if result or not report.get("ready_for_batch_wiring"):
        raise RuntimeError("Collector readiness audit did not pass; resolve its report before a batch run")
    return report


def state_path(status_root: Path) -> Path:
    return status_root / "manager_state.json"


def load_state(status_root: Path) -> dict[str, Any]:
    path = state_path(status_root)
    return read_json(path) if path.exists() else {"runs": {}, "updated_at": ""}


def save_state(status_root: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    atomic_json(state_path(status_root), state)


def command_plan(args: argparse.Namespace) -> int:
    targets = build_targets(args.slug, all_targets=args.all)
    counts: dict[str, int] = {}
    for target in targets:
        counts[target["kind"]] = counts.get(target["kind"], 0) + 1
        print(f"{target['slug']:<28} {target['kind']:<9} {target['effective_adapter'] if target['kind'] == 'browser' else target['adapter']}")
    print(f"\n{len(targets)} jurisdiction(s): " + ", ".join(f"{value} {key}" for key, value in sorted(counts.items())))
    return 0


def command_status(args: argparse.Namespace) -> int:
    state = load_state(args.status_root)
    runs = state.get("runs", {})
    for slug in sorted(runs):
        item = runs[slug]
        print(f"{slug:<28} {item.get('status', 'unknown'):<10} {item.get('finished_at', '')} {item.get('error', '')}")
    print(f"{len(runs)} tracked jurisdiction(s); state: {state_path(args.status_root)}")
    return 0


def command_run(args: argparse.Namespace) -> int:
    targets = build_targets(args.slug, all_targets=args.all)
    if not args.skip_readiness_check:
        readiness = readiness_check(targets, all_targets=args.all)
        print(f"Readiness gate passed: {readiness['completed_jurisdictions']}/{readiness['expected_jurisdictions']}")
    if args.dry_run:
        for target in targets:
            print(f"DRY RUN {target['slug']}: {target['kind']} -> {args.output_root / target['slug']}")
        return 0

    # Deliberately sequential.  A browser collector exposes normal publisher
    # verification in a visible Chrome window; sharing it across workers would
    # create unsafe concurrent traffic and profile contention.
    state = load_state(args.status_root)
    state.setdefault("runs", {})
    failures = 0
    for index, target in enumerate(targets, 1):
        slug = target["slug"]
        prior = state["runs"].get(slug, {})
        if prior.get("status") == "complete" and not args.rerun_complete:
            print(f"SKIP {index}/{len(targets)} {slug} (already complete; use --rerun-complete to refresh)")
            continue
        print(f"START {index}/{len(targets)} {slug} [{target['kind']}]")
        state["runs"][slug] = {"status": "running", "started_at": utc_now(), "target": target}
        save_state(args.status_root, state)
        try:
            outcome = collect_one(target, args.output_root, browser_port=args.browser_port,
                                  max_pages=args.max_pages, municode_delay=args.municode_delay)
            state["runs"][slug].update({"status": "complete", "finished_at": utc_now(), **outcome})
            print(f"DONE  {index}/{len(targets)} {slug}")
        except KeyboardInterrupt:
            state["runs"][slug].update({"status": "interrupted", "finished_at": utc_now()})
            save_state(args.status_root, state)
            print("Interrupted safely; caches/checkpoints remain available for the next run.")
            return 130
        except Exception as exc:
            failures += 1
            state["runs"][slug].update({"status": "failed", "finished_at": utc_now(),
                                         "error": f"{type(exc).__name__}: {exc}",
                                         "traceback": traceback.format_exc()})
            print(f"FAILED {index}/{len(targets)} {slug}: {type(exc).__name__}: {exc}")
        save_state(args.status_root, state)
    print(f"Batch finished: {len(targets) - failures}/{len(targets)} completed this invocation; {failures} failed.")
    return 1 if failures else 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT,
                        help="root for production CSV/JSON exports")
    result.add_argument("--status-root", type=Path, default=DEFAULT_STATUS,
                        help="root for resumable manager state")
    sub = result.add_subparsers(dest="command", required=True)
    for command in ("plan", "run"):
        item = sub.add_parser(command)
        item.add_argument("--slug", action="append", help="one jurisdiction key; repeatable")
        item.add_argument("--all", action="store_true", help="select every current workbook jurisdiction (fail closed)")
    run = sub.choices["run"]
    run.add_argument("--dry-run", action="store_true", help="show selected routes without collection")
    run.add_argument("--skip-readiness-check", action="store_true", help="bypass the local completion-evidence gate")
    run.add_argument("--rerun-complete", action="store_true", help="refresh a jurisdiction marked complete in the manager ledger")
    run.add_argument("--browser-port", type=int, default=9237, help="Chrome DevTools port for one visible browser session")
    run.add_argument("--max-pages", type=int, default=50000, help="browser collector per-jurisdiction page safety limit")
    run.add_argument("--municode-delay", type=float, default=0.5, help="seconds between uncached Municode API calls")
    sub.add_parser("status", help="show the durable manager ledger")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "plan":
        return command_plan(args)
    if args.command == "status":
        return command_status(args)
    return command_run(args)


if __name__ == "__main__":
    raise SystemExit(main())

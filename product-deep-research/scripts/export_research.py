"""Validate, stage and publish immutable reports plus an append-only competitor workbook."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from research_core import digest, product_id, safe_screenshot, slug, utf8_console
from report_writer import write_report
from validate_research import load_json, validate
from workbook_writer import append_run, format_database, history_index, open_database


def file_hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


@contextmanager
def storage_lock(root: Path):
    path = root / ".export.lock"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ValueError(f"Storage is locked: {path}. Close the other exporter. Remove a stale lock only after confirming its process has stopped.") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "started_utc": datetime.now(timezone.utc).isoformat()}))
        yield
    finally:
        path.unlink(missing_ok=True)


def run_directory(root: Path, data: dict) -> Path:
    p, r = data["product"], data["research"]
    return root / slug(p["industry"]) / f"{slug(p['name'])}-{product_id(p)[4:12]}" / f"{r['date']}_{r['run_id']}"


def verify_existing(record: dict, data: dict, input_base: Path, root: Path) -> dict:
    if record["dataset_sha256"] != digest(data):
        raise ValueError("Run ID already exists with different data. Use a new run_id to preserve history.")
    dataset = Path(record["dataset_path"]).resolve()
    report = Path(record["report_path"]).resolve()
    if not dataset.is_relative_to(root) or not report.is_relative_to(root):
        raise ValueError("Existing history points outside the selected storage root")
    manifest_path = dataset.parent / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Incomplete previous export: {manifest_path} missing; do not overwrite; restore from backup or use a new run_id")
    manifest = load_json(manifest_path)
    if manifest.get("dataset_sha256") != digest(data):
        raise ValueError("Existing manifest does not match this dataset")
    if not isinstance(manifest.get("files"), dict) or not {"report.docx", "research.json"}.issubset(manifest["files"]):
        raise ValueError("Incomplete artifact manifest; report.docx and research.json checksums are required")
    for name, checksum in manifest["files"].items():
        target = (dataset.parent / name).resolve()
        if not target.is_relative_to(dataset.parent) or not target.is_file() or file_hash(target) != checksum:
            raise ValueError(f"Existing artifact missing or changed: {target}")
    for ev in data["evidence"]:
        if ev["screenshot"] and file_hash(safe_screenshot(input_base, ev["screenshot"])) != manifest["files"].get(ev["screenshot"]):
            raise ValueError("Screenshot changed for an existing run; use a new run_id")
    return {"product_id": product_id(data["product"]), "run_id": data["research"]["run_id"],
            "report": str(report), "research_json": str(dataset), "screenshots": str(dataset.parent / "screenshots"),
            "manifest": str(manifest_path), "already_exported": True}


def export_files(inputs: list[Path], storage_root: Path | None = None, *, strict_gaps: bool = False) -> dict:
    root = (storage_root or Path(os.environ.get("PRODUCT_RESEARCH_HOME", "~/product-research"))).expanduser().resolve()
    datasets = []
    warnings: list[str] = []
    seen = set()
    # Validate the entire batch before creating storage or writing any output.
    for input_path in inputs:
        input_path = input_path.resolve()
        data = load_json(input_path)
        result = validate(data, input_path.parent, strict_gaps=strict_gaps)
        result.require_valid()
        warnings.extend(f"{input_path.name}: {warning}" for warning in result.warnings)
        key = product_id(data["product"]), data["research"]["run_id"]
        if key in seen:
            raise ValueError(f"Duplicate product/run in export batch: {key}")
        seen.add(key)
        datasets.append((input_path, data, key))
    if not datasets:
        raise ValueError("At least one research dataset is required")
    root.mkdir(parents=True, exist_ok=True)
    with storage_lock(root):
        database = root / "competitors.xlsx"
        wb = open_database(database)
        try:
            history = history_index(wb)
            outputs = []
            pending = []
            for input_path, data, key in datasets:
                if key in history:
                    outputs.append(verify_existing(history[key], data, input_path.parent, root))
                    continue
                final = run_directory(root, data)
                if not final.resolve().is_relative_to(root):
                    raise ValueError(f"Run path escapes storage root through a symlink: {final}")
                if final.exists():
                    raise ValueError(f"Unindexed run directory already exists: {final}. Preserve it; inspect an interrupted export before retrying.")
                pending.append((input_path, data, final))
            if not pending:
                return {"database": str(database), "runs": outputs, "warnings": warnings}
            stage_root = Path(tempfile.mkdtemp(prefix=".export-", dir=root))
            published: list[Path] = []
            try:
                staged = []
                for i, (input_path, data, final) in enumerate(pending):
                    stage = stage_root / str(i)
                    stage.mkdir()
                    (stage / "screenshots").mkdir()
                    for ev in data["evidence"]:
                        if ev["screenshot"]:
                            target = safe_screenshot(stage, ev["screenshot"])
                            target.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(safe_screenshot(input_path.parent, ev["screenshot"]), target)
                    (stage / "research.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
                    write_report(data, stage / "report.docx", stage)
                    files = {p.relative_to(stage).as_posix(): file_hash(p) for p in stage.rglob("*") if p.is_file()}
                    manifest = {"schema_version": "1.0", "product_id": product_id(data["product"]),
                        "run_id": data["research"]["run_id"], "dataset_sha256": digest(data), "files": files}
                    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                    append_run(wb, data, final / "report.docx", final / "research.json")
                    staged.append((stage, final))
                    outputs.append({"product_id": manifest["product_id"], "run_id": manifest["run_id"],
                        "report": str(final / "report.docx"), "research_json": str(final / "research.json"),
                        "screenshots": str(final / "screenshots"), "manifest": str(final / "manifest.json"), "already_exported": False})
                format_database(wb)
                staged_book = stage_root / "competitors.xlsx"
                wb.save(staged_book)
                # Read back the serialized workbook before publication.
                check = open_database(staged_book)
                try:
                    history_index(check)
                finally:
                    check.close()
                if database.exists():
                    backup_dir = root / ".backups"
                    if not backup_dir.resolve().is_relative_to(root):
                        raise ValueError("Backup directory escapes storage root through a symlink")
                    backup_dir.mkdir(exist_ok=True)
                    backup = backup_dir / f"competitors-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}.xlsx"
                    shutil.copy2(database, backup)
                for stage, final in staged:
                    final.parent.mkdir(parents=True, exist_ok=True)
                    stage.rename(final)
                    published.append(final)
                # Atomic workbook replacement is the transaction's commit point.
                os.replace(staged_book, database)
            except BaseException:
                for path in published:
                    if path.resolve().is_relative_to(root) and path != root:
                        shutil.rmtree(path)
                raise
            finally:
                if stage_root.resolve().is_relative_to(root):
                    shutil.rmtree(stage_root, ignore_errors=True)
            return {"database": str(database), "runs": outputs, "warnings": warnings}
        finally:
            wb.close()


def main() -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_json", nargs="+", type=Path, help="One JSON per product; batch exports share a single transaction")
    parser.add_argument("--storage-root", type=Path, help="Default PRODUCT_RESEARCH_HOME or ~/product-research")
    parser.add_argument("--strict-gaps", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(export_files(args.research_json, args.storage_root, strict_gaps=args.strict_gaps), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"Export error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

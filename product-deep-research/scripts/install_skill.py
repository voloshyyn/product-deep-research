"""Install a reviewed skill copy, refusing any existing destination. Standard library only."""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from research_core import utf8_console

NAME = "product-deep-research"


def install(destination: Path, source: Path | None = None) -> Path:
    source = (source or Path(__file__).resolve().parents[1]).resolve()
    destination = destination.expanduser().absolute()
    if destination.name != NAME:
        raise ValueError(f"Destination directory must be named {NAME}")
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"Destination already exists; nothing overwritten: {destination}")
    if destination.resolve().is_relative_to(source):
        raise ValueError("Cannot install a skill inside itself")
    required = ["SKILL.md", "requirements.txt", "scripts/export_research.py", "scripts/validate_research.py", "references/research-schema.json"]
    for relative in required:
        if not (source / relative).is_file():
            raise ValueError(f"Incomplete skill: {relative}")
    manifest = (source / "SKILL.md").read_text(encoding="utf-8")
    if not manifest.startswith("---\n") or f"name: {NAME}\n" not in manifest.split("---", 2)[1]:
        raise ValueError("Invalid skill frontmatter")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".skill-install-", dir=destination.parent))
    try:
        copy = stage / NAME
        shutil.copytree(source, copy, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".venv", ".qa"))
        # A new destination only; recheck to avoid an accidental existing-skill update.
        if destination.exists() or destination.is_symlink():
            raise ValueError("Destination appeared during installation; nothing overwritten")
        copy.rename(destination)
    finally:
        if stage.resolve().is_relative_to(destination.parent.resolve()):
            shutil.rmtree(stage, ignore_errors=True)
    return destination.resolve()


def main() -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path.home() / ".agents" / "skills" / NAME)
    parser.add_argument("--check", action="store_true", help="Read-only structural install check; does not prove live Codex discovery")
    args = parser.parse_args()
    try:
        if args.check:
            target = args.destination.expanduser().resolve()
            if not (target / "SKILL.md").is_file():
                raise ValueError(f"Skill not installed: {target}")
            print(f"Installed manifest: {target / 'SKILL.md'}")
        else:
            print(f"Installed: {install(args.destination)}")
        print("Restart Codex if necessary, open /skills, and invoke $product-deep-research to verify host discovery.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Install error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

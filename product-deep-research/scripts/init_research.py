"""Create a gap-explicit research scaffold without inventing findings."""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import date
from pathlib import Path

from research_core import CATEGORIES, normalize_url, utf8_console


def scaffold(name: str, url: str, industry: str, market: str, *, language: str = "ru",
             depth: str = "standard", requirements: list[str] | None = None) -> dict:
    normalize_url(url)
    ru = language.split("-")[0] == "ru"
    pending = "Исследование еще не выполнено" if ru else "Research has not been performed yet"
    reqs = [{"id": f"custom-{i}", "title": request, "request": request}
            for i, request in enumerate(requirements or [], 1)]
    return {
        "schema_version": "1.0",
        "product": {"name": name, "url": url, "regional_variant": "", "industry": industry, "market": market},
        "research": {"run_id": uuid.uuid4().hex[:12], "date": date.today().isoformat(), "language": language,
            "depth": depth, "objectives": ["Исследовать продукт по всем обязательным и дополнительным критериям" if ru else "Research all standard and additional criteria"],
            "methodology": pending, "comparison_group": "", "competitor_urls": [], "additional_requirements": reqs},
        "sources": [], "evidence": [], "claims": [],
        "sections": [{"category": key, "claim_ids": [], "limitation": pending} for key in CATEGORIES],
        "custom_sections": [{"requirement_id": r["id"], "claim_ids": [], "limitation": pending} for r in reqs],
        "journeys": [{"id": f"journey-{i}", "title": title, "goal": title, "status": "NOT_TESTED",
                      "steps": [], "evidence_ids": [], "limitation": pending} for i, title in enumerate(
                          (["Поиск решения", "Выбор продукта или услуги", "Начало конверсии"] if ru else
                           ["Discover a solution", "Select a product or service", "Begin conversion"]), 1)],
        "ux_issues": [], "recommendations": [], "executive_summary": [], "conclusions": [], "limitations": [pending],
    }


def main() -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--industry", default="unspecified")
    parser.add_argument("--market", default="unspecified")
    parser.add_argument("--language", default="ru")
    parser.add_argument("--depth", choices=["brief", "standard", "deep"], default="standard")
    parser.add_argument("--requirement", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = scaffold(args.name, args.url, args.industry, args.market, language=args.language,
                        depth=args.depth, requirements=args.requirement)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(args.output.resolve())
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Initialization error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

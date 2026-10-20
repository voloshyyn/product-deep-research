"""JSON Schema and semantic evidence validation. Exit 2 means invalid input."""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from research_core import CATEGORIES, normalize_url, safe_screenshot, utf8_console

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "references" / "research-schema.json"


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def require_valid(self) -> None:
        if self.errors:
            raise ValueError("Research validation failed:\n" + "\n".join(self.errors))


def load_json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict:
        result: dict = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"Non-finite JSON number: {value}")

    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=pairs,
                      parse_constant=reject_constant)


def validate(data: dict, base_dir: Path | None = None, *, strict_gaps: bool = False) -> ValidationResult:
    result = ValidationResult()
    schema = load_json(SCHEMA_PATH)
    for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data):
        location = "/".join(map(str, error.absolute_path)) or "$"
        result.errors.append(f"{location}: {error.message}")
    if result.errors:
        return result

    def check_values(value: Any, location: str = "$") -> None:
        if isinstance(value, float) and not math.isfinite(value):
            result.errors.append(f"{location}: non-finite number")
        if isinstance(value, str) and any((ord(c) < 32 and c not in "\t\n\r") or
                0xD800 <= ord(c) <= 0xDFFF or ord(c) in {0xFFFE, 0xFFFF} for c in value):
            result.errors.append(f"{location}: invalid XML/Excel control character")
        if isinstance(value, dict):
            for key, item in value.items():
                check_values(item, f"{location}/{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                check_values(item, f"{location}/{i}")
    check_values(data)

    def fail(message: str) -> None:
        result.errors.append(message)

    def gap(message: str) -> None:
        (result.errors if strict_gaps else result.warnings).append(message)

    def index(items: list[dict], name: str, key: str = "id") -> dict:
        output: dict = {}
        for item in items:
            identifier = item[key]
            if identifier in output:
                fail(f"{name}: duplicate {key} {identifier}")
            output[identifier] = item
        return output

    sources = index(data["sources"], "sources")
    evidence = index(data["evidence"], "evidence")
    claims = index(data["claims"], "claims")
    requirements = index(data["research"]["additional_requirements"], "additional_requirements")
    for name in ("journeys", "ux_issues", "recommendations"):
        index(data[name], name)
    sections = index(data["sections"], "sections", "category")
    custom = index(data["custom_sections"], "custom_sections", "requirement_id")
    if set(sections) != set(CATEGORIES):
        fail("sections: all 15 standard categories must appear exactly once")
    if set(custom) != set(requirements):
        fail("custom_sections: must cover every additional requirement exactly once")

    run_date = data["research"]["date"]
    lang = data["research"]["language"].split("-")[0]
    if lang not in {"ru", "en"}:
        from report_writer import LABELS
        missing = (set(LABELS["en"]) | set(CATEGORIES)) - set(data.get("labels", {}))
        if missing:
            fail("labels: complete report translations required for this language: " + ", ".join(sorted(missing)))
    if run_date > date.today().isoformat():
        fail("research/date: may not be in the future")
    all_urls = [data["product"]["url"], *data["research"]["competitor_urls"]]
    all_urls += [s["url"] for s in sources.values()]
    all_urls += [s["url"] for j in data["journeys"] for s in j["steps"]]
    all_urls += [i["page_url"] for i in data["ux_issues"]]
    for url in all_urls:
        try:
            normalize_url(url)
        except (ValueError, UnicodeError) as exc:
            fail(f"URL {url}: {exc}")

    for sid, source in sources.items():
        if source["accessed_on"] > run_date:
            fail(f"source {sid}: access date is after research date")
        if source["access_status"] == "NOT_ACCESSIBLE":
            gap(f"source {sid}: NOT_ACCESSIBLE — {source['access_detail']}")

    for eid, ev in evidence.items():
        source = sources.get(ev["source_id"])
        if source is None:
            fail(f"evidence {eid}: unknown source {ev['source_id']}")
            continue
        if source["access_status"] != "ACCESSED":
            fail(f"evidence {eid}: inaccessible sources cannot support evidence")
        if not source["accessed_on"] <= ev["verified_on"] <= run_date:
            fail(f"evidence {eid}: invalid verification chronology")
        if ev["kind"] == "FIRST_PARTY_STATEMENT" and source["publisher_type"] != "FIRST_PARTY":
            fail(f"evidence {eid}: first-party statement requires FIRST_PARTY source")
        if ev["kind"] == "INDEPENDENT_CORROBORATION" and source["publisher_type"] != "INDEPENDENT":
            fail(f"evidence {eid}: independent corroboration requires INDEPENDENT source")
        if ev["screenshot"]:
            try:
                path = safe_screenshot(base_dir or Path.cwd(), ev["screenshot"])
                if base_dir is None or not path.is_file():
                    raise ValueError("Referenced screenshot does not exist (provide dataset base directory)")
                from docx.image.image import Image
                picture = Image.from_file(str(path))
                if picture.px_width <= 0 or picture.px_height <= 0:
                    raise ValueError("Invalid screenshot dimensions")
            except Exception as exc:
                fail(f"evidence {eid}: {exc}")

    covered: set[str] = set()
    for section in [*data["sections"], *data["custom_sections"]]:
        key = section.get("category", section.get("requirement_id"))
        if not section["claim_ids"] and not section["limitation"].strip():
            fail(f"section {key}: needs claims or an explicit limitation")
        if section["limitation"].strip():
            gap(f"section {key}: {section['limitation']}")
        for cid in section["claim_ids"]:
            claim = claims.get(cid)
            if claim is None:
                fail(f"section {key}: unknown claim {cid}")
                continue
            covered.add(cid)
            if "category" in section and claim["category"] != key:
                fail(f"section {key}: claim {cid} belongs to another category")
            if "requirement_id" in section and claim["custom_requirement_id"] != key:
                fail(f"section {key}: claim {cid} belongs to another custom requirement")

    for cid, claim in claims.items():
        if cid not in covered:
            fail(f"claim {cid}: not included in its report section")
        if claim["verified_on"] > run_date:
            fail(f"claim {cid}: verification date is after research date")
        if (claim["category"] == "custom") != (claim["custom_requirement_id"] is not None):
            fail(f"claim {cid}: custom category and requirement ID must be paired")
        if claim["custom_requirement_id"] is not None and claim["custom_requirement_id"] not in requirements:
            fail(f"claim {cid}: unknown custom requirement")
        for sid in claim["source_ids"]:
            if sid not in sources:
                fail(f"claim {cid}: unknown source {sid}")
        linked = [evidence[eid] for eid in claim["evidence_ids"] if eid in evidence]
        if len(linked) != len(claim["evidence_ids"]):
            fail(f"claim {cid}: unknown evidence ID")
        for ev in linked:
            if ev["source_id"] not in claim["source_ids"]:
                fail(f"claim {cid}: evidence source missing from source_ids")
            if ev["verified_on"] > claim["verified_on"]:
                fail(f"claim {cid}: evidence postdates claim verification")
        status = claim["status"]
        kinds = {e["kind"] for e in linked}
        if status in {"VERIFIED", "PARTIALLY_VERIFIED"}:
            if not linked:
                fail(f"claim {cid}: supported claims require evidence")
            linked_sources = {e["source_id"] for e in linked}
            if set(claim["source_ids"]) != linked_sources:
                fail(f"claim {cid}: each supporting source must have linked evidence")
            if claim["kind"] == "INTERPRETATION":
                fail(f"claim {cid}: interpretations must be HYPOTHESIS")
            if claim["kind"] == "COMPANY_CLAIM" and "FIRST_PARTY_STATEMENT" not in kinds:
                fail(f"claim {cid}: company claims require first-party statement evidence")
            if claim["kind"] == "OBSERVATION" and "DIRECT_OBSERVATION" not in kinds:
                fail(f"claim {cid}: observations require direct observation evidence")
            if claim["kind"] == "FACT" and not kinds.intersection({"DIRECT_OBSERVATION", "INDEPENDENT_CORROBORATION"}):
                fail(f"claim {cid}: company statements alone cannot establish an independent fact")
            if status == "PARTIALLY_VERIFIED" and not claim["qualification"].strip():
                fail(f"claim {cid}: partial verification requires qualification")
        elif status == "HYPOTHESIS":
            if claim["kind"] != "INTERPRETATION" or not claim["qualification"].strip():
                fail(f"claim {cid}: hypotheses require INTERPRETATION and reasoning/qualification")
            if not linked:
                fail(f"claim {cid}: hypotheses need evidence for their premises")
        else:
            if not claim["gap_reason"].strip():
                fail(f"claim {cid}: missing information requires a gap reason")
            if claim["value"] is not None or claim["unit"]:
                fail(f"claim {cid}: unsupported claims cannot carry factual values")
            if claim["confidence"] != "LOW":
                fail(f"claim {cid}: unsupported claims must have LOW confidence")
            if status == "NOT_ACCESSIBLE" and not any(
                sources.get(s, {}).get("access_status") == "NOT_ACCESSIBLE" for s in claim["source_ids"]
            ):
                fail(f"claim {cid}: NOT_ACCESSIBLE needs a documented inaccessible source")
            gap(f"claim {cid}: {status} — {claim['gap_reason']}")

    def check_refs(refs: list[str], where: str) -> None:
        for cid in refs:
            if cid not in claims:
                fail(f"{where}: unknown claim {cid}")

    for field_name in ("executive_summary", "conclusions"):
        check_refs(data[field_name], field_name)
    if not 3 <= len(data["journeys"]) <= 5:
        gap("journeys: default is 3–5; document the reason for adjusted coverage in limitations")
        if not data["limitations"]:
            fail("journeys: adjusted coverage requires a documented limitation")
    for journey in data["journeys"]:
        for eid in journey["evidence_ids"]:
            if eid not in evidence:
                fail(f"journey {journey['id']}: unknown evidence {eid}")
        if journey["status"] != "TESTED" and not journey["limitation"].strip():
            fail(f"journey {journey['id']}: untested or partial journey needs limitation")
        if journey["status"] in {"TESTED", "PARTIAL"}:
            evs = [evidence[e] for e in journey["evidence_ids"] if e in evidence]
            if not journey["steps"] or not any(e["kind"] == "DIRECT_OBSERVATION" and
                sources.get(e["source_id"], {}).get("access_method") in {"BROWSER", "PLAYWRIGHT"} for e in evs):
                fail(f"journey {journey['id']}: testing requires actual browser observation")
        for step in journey["steps"]:
            check_refs(step["outcome_claim_ids"], f"journey {journey['id']}")
            if journey["status"] == "TESTED" and not step["outcome_claim_ids"]:
                fail(f"journey {journey['id']}: tested step needs an observed outcome")
            if journey["status"] == "TESTED":
                for cid in step["outcome_claim_ids"]:
                    c = claims.get(cid, {})
                    if c.get("kind") != "OBSERVATION" or c.get("status") not in {"VERIFIED", "PARTIALLY_VERIFIED"}:
                        fail(f"journey {journey['id']}: tested outcomes must be supported observations")
                    observed = [evidence[e] for e in c.get("evidence_ids", []) if e in evidence]
                    if not any(e["kind"] == "DIRECT_OBSERVATION" and
                            e["id"] in journey["evidence_ids"] and
                            sources.get(e["source_id"], {}).get("access_method") in {"BROWSER", "PLAYWRIGHT"} and
                            sources.get(e["source_id"], {}).get("url") == step["url"] for e in observed):
                        fail(f"journey {journey['id']}: tested step URL needs linked browser observation of that page")
    for issue in data["ux_issues"]:
        check_refs([issue["claim_id"]], f"UX issue {issue['id']}")
        claim = claims.get(issue["claim_id"], {})
        if claim.get("status") not in {"VERIFIED", "PARTIALLY_VERIFIED", "HYPOTHESIS"}:
            fail(f"UX issue {issue['id']}: unsupported UX finding; record it as a limitation")
        if not any(sources.get(evidence.get(e, {}).get("source_id"), {}).get("url") == issue["page_url"]
                   for e in claim.get("evidence_ids", [])):
            fail(f"UX issue {issue['id']}: page URL needs linked evidence for that page")
    for rec in data["recommendations"]:
        check_refs(rec["claim_ids"], f"recommendation {rec['id']}")
        if not rec["claim_ids"]:
            fail(f"recommendation {rec['id']}: needs supporting findings")
    return result


def main() -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_json", type=Path)
    parser.add_argument("--strict-gaps", action="store_true", help="Treat documented gaps as errors")
    args = parser.parse_args()
    try:
        data = load_json(args.research_json)
        result = validate(data, args.research_json.resolve().parent, strict_gaps=args.strict_gaps)
        print(json.dumps({"valid": result.valid, "errors": result.errors, "warnings": result.warnings}, ensure_ascii=False, indent=2))
        return 0 if result.valid else 2
    except (OSError, ValueError) as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Synthetic product evidence for tests only. No network calls or production writes."""
from __future__ import annotations

import base64
import json
from pathlib import Path

from research_core import CATEGORIES

DAY = "2025-01-15"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aNecAAAAASUVORK5CYII=")


def dataset(*, name="Synthetic Atlas", url="https://atlas.example/product", industry="education",
            run="run-001", custom=True, screenshot=False, language="en") -> dict:
    claims = []
    for i, category in enumerate(CATEGORIES, 1):
        claims.append({"id": f"c{i}", "category": category, "title": f"Synthetic {category}",
            "statement": f"Synthetic observation for {category}; test data only.",
            "kind": "OBSERVATION", "status": "VERIFIED", "confidence": "HIGH", "verified_on": DAY,
            "source_ids": ["s1"], "evidence_ids": ["e1"], "qualification": "", "gap_reason": "",
            "custom_requirement_id": None, "facet": None, "value": None, "unit": ""})
    # Exercise attribution, partial values and hypothesis routing.
    claims[1].update(kind="COMPANY_CLAIM", evidence_ids=["e2"], statement="Synthetic company promise.")
    claims[6].update(value=12.5, unit="USD/month before tax; US region")
    claims[7].update(status="PARTIALLY_VERIFIED", qualification="Only the public tier was inspected.", value=99, unit="USD")
    claims[-1].update(kind="INTERPRETATION", status="HYPOTHESIS", confidence="MEDIUM",
                      qualification="Synthetic premise suggests an untested opportunity.", facet="opportunity", value=50)
    if custom:
        claims.append({**claims[0], "id": "custom-c", "category": "custom", "title": "Synthetic custom finding",
                       "custom_requirement_id": "custom-1"})
    return {
        "schema_version": "1.0", "product": {"name": name, "url": url, "industry": industry, "market": "US", "regional_variant": ""},
        "research": {"run_id": run, "date": DAY, "language": language, "depth": "standard",
            "objectives": ["Exercise synthetic export only"], "methodology": "Synthetic fixture, not real research.",
            "comparison_group": "synthetic-comparison", "competitor_urls": ["https://competitor.example"],
            "additional_requirements": [{"id": "custom-1", "title": "Arbitrary integration criterion", "request": "Inspect a user-defined integration"}] if custom else []},
        "sources": [{"id": "s1", "url": url, "title": "Synthetic official page", "publisher_type": "FIRST_PARTY",
            "independence_group": "synthetic-company", "access_status": "ACCESSED", "accessed_on": DAY,
            "access_method": "PLAYWRIGHT", "access_detail": "Synthetic fixture only; no page was actually visited."}],
        "evidence": [{"id": "e1", "source_id": "s1", "kind": "DIRECT_OBSERVATION", "verified_on": DAY,
            "detail": "Synthetic interaction observation.", "locator": "Synthetic selector; desktop 1280x800.",
            "screenshot": "screenshots/synthetic.png" if screenshot else None},
            {"id": "e2", "source_id": "s1", "kind": "FIRST_PARTY_STATEMENT", "verified_on": DAY,
             "detail": "Synthetic attributed statement.", "locator": "Synthetic heading.", "screenshot": None}],
        "claims": claims,
        "sections": [{"category": cat, "claim_ids": [f"c{i}"], "limitation": ""} for i, cat in enumerate(CATEGORIES, 1)],
        "custom_sections": [{"requirement_id": "custom-1", "claim_ids": ["custom-c"], "limitation": ""}] if custom else [],
        "journeys": [{"id": f"j{i}", "title": f"Synthetic journey {i}", "goal": "Exercise export",
            "status": "TESTED", "steps": [{"action": "Synthetic test action", "url": url, "outcome_claim_ids": ["c1"]}],
            "evidence_ids": ["e1"], "limitation": ""} for i in range(1, 4)],
        "ux_issues": [{"id": "ux1", "title": "Synthetic UX issue", "claim_id": "c11", "page_url": url,
            "heuristics": [1, 9], "severity": 2, "severity_rationale": "Synthetic minor friction with workaround.",
            "impact": "Potential extra task effort; not a measured population effect.", "recommendation": "Test clearer feedback.",
            "priority": "P2", "wcag": ["3.3.1"]}],
        "recommendations": [{"id": "r1", "title": "Improve feedback", "action": "Prototype and test clearer feedback.",
            "rationale": "Synthetic observed friction.", "priority": "P2", "claim_ids": ["c11"]}],
        "executive_summary": ["c1", "c15"], "conclusions": ["c1"], "limitations": ["All data are synthetic; no product research performed."],
    }


def write_dataset(folder: Path, data: dict) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    if any(ev["screenshot"] for ev in data["evidence"]):
        (folder / "screenshots").mkdir(exist_ok=True)
        (folder / "screenshots" / "synthetic.png").write_bytes(PNG)
    output = folder / "research.json"
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return output

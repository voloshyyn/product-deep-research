import copy
import json

import pytest
from jsonschema import Draft202012Validator

from fixtures import dataset, write_dataset
from init_research import scaffold
from research_core import CATEGORIES, normalize_url, product_id, slug
from validate_research import SCHEMA_PATH, load_json, validate


def test_schema_itself_is_valid():
    Draft202012Validator.check_schema(load_json(SCHEMA_PATH))


def test_valid_and_screenshot(tmp_path):
    data = dataset(screenshot=True)
    write_dataset(tmp_path, data)
    result = validate(data, tmp_path, strict_gaps=True)
    assert result.valid, result.errors


@pytest.mark.parametrize("mutation,fragment", [
    (lambda d: d["claims"][0].update(evidence_ids=[]), "require evidence"),
    (lambda d: d["claims"][0].update(evidence_ids=["missing"]), "unknown evidence"),
    (lambda d: d["evidence"][0].update(source_id="missing"), "unknown source"),
    (lambda d: d["sources"][0].update(access_status="NOT_ACCESSIBLE"), "inaccessible sources"),
    (lambda d: d["claims"][0].update(status="PARTIALLY_VERIFIED"), "requires qualification"),
    (lambda d: d["claims"][0].update(kind="INTERPRETATION"), "must be HYPOTHESIS"),
    (lambda d: d["claims"][0].update(status="HYPOTHESIS"), "require INTERPRETATION"),
    (lambda d: d["claims"][0].update(kind="FACT", evidence_ids=["e2"]), "cannot establish"),
    (lambda d: d["evidence"][0].update(kind="INDEPENDENT_CORROBORATION"), "requires INDEPENDENT"),
    (lambda d: d["claims"][0].update(source_ids=[]), "source missing"),
    (lambda d: d["claims"][0].update(verified_on="2024-01-01"), "postdates"),
    (lambda d: d["sources"][0].update(accessed_on="2026-01-01"), "after research"),
    (lambda d: d["claims"][0].update(verified_on="2025-02-30"), "not a 'date'"),
    (lambda d: d["claims"].append(copy.deepcopy(d["claims"][0])), "duplicate"),
    (lambda d: d["sections"][0].update(category="pricing"), "all 15"),
    (lambda d: d["sections"][0].update(claim_ids=[]), "needs claims"),
    (lambda d: d["custom_sections"].clear(), "every additional"),
    (lambda d: d["claims"][-1].update(custom_requirement_id="missing"), "unknown custom"),
    (lambda d: d["ux_issues"][0].update(severity=5), "greater than"),
    (lambda d: d["journeys"][0].update(evidence_ids=[]), "actual browser"),
    (lambda d: d["journeys"][0]["steps"][0].update(outcome_claim_ids=[]), "observed outcome"),
    (lambda d: d["sources"][0].update(access_method="WEB"), "actual browser"),
    (lambda d: d["product"].update(url="https://user:password@atlas.example"), "without credentials"),
    (lambda d: d.update(unexpected="value"), "Additional properties"),
    (lambda d: d["executive_summary"].append("missing"), "unknown claim"),
])
def test_invalid_evidence_rejected(mutation, fragment, tmp_path):
    data = dataset()
    mutation(data)
    result = validate(data, tmp_path)
    assert not result.valid
    assert fragment in "\n".join(result.errors)


def test_explicit_gaps_allowed_as_warnings_and_strict_errors(tmp_path):
    data = dataset()
    data["claims"][2].update(status="UNVERIFIED", confidence="LOW", evidence_ids=[], source_ids=[], gap_reason="No reliable demographics")
    result = validate(data, tmp_path)
    assert result.valid, result.errors
    assert any("UNVERIFIED" in w for w in result.warnings)
    assert not validate(data, tmp_path, strict_gaps=True).valid


def test_inaccessible_claim_has_documented_source(tmp_path):
    data = dataset()
    data["sources"].append({**data["sources"][0], "id": "blocked", "access_status": "NOT_ACCESSIBLE", "access_detail": "HTTP 403"})
    data["claims"][2].update(status="NOT_ACCESSIBLE", confidence="LOW", evidence_ids=[], source_ids=["blocked"], gap_reason="HTTP 403")
    assert validate(data, tmp_path).valid
    data["claims"][2]["value"] = 4000
    assert not validate(data, tmp_path).valid


@pytest.mark.parametrize("path", ["screenshots/../../secret.png", "screenshots/../outside.png", "screenshots/C:/x.png", "screenshots/missing.png"])
def test_screenshot_paths_rejected(path, tmp_path):
    data = dataset()
    data["evidence"][0]["screenshot"] = path
    assert not validate(data, tmp_path).valid


def test_duplicate_keys_and_nonfinite_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"x": 1, "x": 2}')
    with pytest.raises(ValueError, match="Duplicate JSON"):
        load_json(path)
    path.write_text('{"x": NaN}')
    with pytest.raises(ValueError, match="Non-finite"):
        load_json(path)


def test_scaffold_covers_custom_and_default_language(tmp_path):
    data = scaffold("Demo", "https://demo.example", "healthcare", "UA", requirements=["Check telehealth", "Check matching"])
    assert data["research"]["language"] == "ru"
    assert len(data["sections"]) == 15
    assert len(data["custom_sections"]) == 2
    result = validate(data, tmp_path)
    assert result.valid, result.errors
    assert result.warnings


def test_normalized_identity_and_regional_variants():
    a = dataset()["product"]
    b = {**a, "url": "http://WWW.atlas.example:80/product/?utm_source=x#section", "name": "Rebranded"}
    assert product_id(a) == product_id(b)
    assert product_id(a) == product_id({**a, "market": "UK", "industry": "finance"})
    assert product_id(a) != product_id({**a, "regional_variant": "UK offering"})
    assert product_id(a) != product_id({**a, "url": "https://atlas.example/uk/product"})
    assert normalize_url("https://atlas.example/product?z=2&a=1&fbclid=3") == "https://atlas.example/product?a=1&z=2"
    assert slug("CON") != "con"
    assert "/" not in slug("../../My Product")


@pytest.mark.parametrize("mutate,fragment", [
    (lambda d: d["journeys"][0]["steps"][0].update(url="https://unvisited.example"), "step URL"),
    (lambda d: d["ux_issues"][0].update(page_url="https://unvisited.example"), "page URL"),
    (lambda d: d["claims"][0].update(statement="bad\x00text"), "control character"),
    (lambda d: d["claims"][0].update(value=float("inf")), "non-finite"),
    (lambda d: d["research"].update(language="de"), "translations required"),
])
def test_additional_integrity_checks(mutate, fragment, tmp_path):
    data = dataset()
    mutate(data)
    result = validate(data, tmp_path)
    assert not result.valid
    assert fragment in "\n".join(result.errors)


def test_other_language_translation_dictionary(tmp_path):
    from report_writer import LABELS
    data = dataset(language="de")
    data["labels"] = {key: f"Testübersetzung {key}" for key in set(LABELS["en"]) | set(CATEGORIES)}
    assert validate(data, tmp_path).valid

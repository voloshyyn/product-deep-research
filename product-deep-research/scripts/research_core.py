"""Shared identifiers, category routing and workbook contracts (no network I/O)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CATEGORIES = {
    "overview": ("Product overview", "Обзор продукта", "Overview"),
    "positioning": ("Positioning and value proposition", "Позиционирование и ценностное предложение", "Overview"),
    "audience_jtbd": ("Audience and JTBD", "Аудитория и JTBD", "Audience & JTBD"),
    "customer_problems": ("Customer problems", "Проблемы клиентов", "Audience & JTBD"),
    "functionality": ("Product functionality", "Функциональность", "Features & Services"),
    "products_services": ("Products and services", "Продукты и услуги", "Features & Services"),
    "pricing": ("Pricing and plans", "Цены и тарифы", "Pricing & Business"),
    "business_model": ("Business model", "Бизнес модель", "Pricing & Business"),
    "marketing": ("Marketing and acquisition", "Маркетинг и привлечение", "Marketing"),
    "user_journeys": ("User journeys", "Пользовательские сценарии", "UX & UI"),
    "ux": ("UX analysis", "Анализ UX", "UX & UI"),
    "ui": ("UI analysis", "Анализ UI", "UX & UI"),
    "accessibility": ("Accessibility and responsive design", "Доступность и адаптивность", "UX & UI"),
    "trust": ("Trust and reputation", "Доверие и репутация", "Overview"),
    "strengths_weaknesses_opportunities": ("Strengths weaknesses and opportunities", "Сильные и слабые стороны и возможности", "Strengths & Weaknesses"),
}

COMMON = ["record_id", "product_id", "product_name", "product_url", "regional_variant",
          "industry", "market", "run_id", "research_date", "comparison_group"]
CLAIM_COLUMNS = ["claim_id", "category", "title", "claim_kind", "facet", "confirmed_fact",
                 "qualified_claim", "hypothesis", "gap", "value", "unit", "qualification",
                 "verification_status", "confidence", "verified_on", "evidence_ids", "source_urls"]
SCHEMAS = {name: COMMON + CLAIM_COLUMNS for name in [
    "Overview", "Audience & JTBD", "Features & Services", "Pricing & Business", "Marketing",
    "UX & UI", "Strengths & Weaknesses", "Opportunities"]}
SCHEMAS["Custom Research"] = COMMON + ["requirement_id", "requirement_title", "user_request"] + CLAIM_COLUMNS
SCHEMAS["Sources"] = COMMON + ["source_id", "source_url", "source_title", "publisher_type",
    "independence_group", "access_status", "accessed_on", "access_method", "access_detail",
    "evidence_id", "evidence_kind", "verified_on", "evidence_detail", "locator", "screenshot",
    "verification_status", "confidence", "linked_claim_ids"]
SCHEMAS["UX Issues"] = COMMON + ["issue_id", "claim_id", "title", "page_url", "heuristics",
    "severity", "severity_rationale", "impact", "recommendation", "priority", "wcag",
    "verification_status", "confidence", "evidence_ids", "source_urls"]
SCHEMAS["Research History"] = COMMON + ["canonical_url", "dataset_sha256", "report_path",
    "dataset_path", "language", "depth", "objectives", "methodology", "limitations",
    "claim_count", "gap_count", "verification_status", "evidence_ids", "source_urls"]

TRACKING = {"gclid", "fbclid", "msclkid", "dclid", "mc_cid", "mc_eid"}


def normalize_url(url: str) -> str:
    """Normalize identity, retaining regional paths/subdomains and meaningful queries.

    http/https and a leading www are identity aliases, not evidence of redirects.
    Exact source URLs are stored unchanged elsewhere. Never remove a locale path.
    """
    p = urlsplit(url.strip())
    if p.scheme.lower() not in {"http", "https"} or not p.hostname or p.username or p.password:
        raise ValueError("Expected an absolute public HTTP(S) URL without credentials")
    host = p.hostname.encode("idna").decode("ascii").lower()
    if host.startswith("www."):
        host = host[4:]
    if ":" in host:
        host = f"[{host}]"
    port = p.port
    if port and not ((p.scheme.lower() == "http" and port == 80) or
                     (p.scheme.lower() == "https" and port == 443)):
        host += f":{port}"
    query = sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                   if not k.lower().startswith("utm_") and k.lower() not in TRACKING)
    return urlunsplit(("https", host, p.path.rstrip("/"), urlencode(query), ""))


def product_id(product: dict) -> str:
    variant = unicodedata.normalize("NFC", product.get("regional_variant", "")).strip().casefold()
    return "prd_" + hashlib.sha256((normalize_url(product["url"]) + "\n" + variant).encode()).hexdigest()[:24]


def slug(value: str) -> str:
    value = unicodedata.normalize("NFC", value).casefold()
    value = re.sub(r"[^\w-]+", "-", value, flags=re.UNICODE).strip("-_")[:64]
    if not value or value.upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]}:
        value = "product-" + hashlib.sha256(value.encode()).hexdigest()[:8]
    return value


def digest(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def safe_screenshot(base: Path, relative: str) -> Path:
    # Reject Windows separators too, even when validating on POSIX.
    if "\\" in relative or ":" in relative:
        raise ValueError("Screenshot must use a relative POSIX path under screenshots/")
    path = (base / relative).resolve()
    root = (base / "screenshots").resolve()
    if not root.is_relative_to(base.resolve()) or not relative.startswith("screenshots/") or not path.is_relative_to(root) or path == root:
        raise ValueError("Screenshot path escapes screenshots/")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise ValueError("Screenshot must be PNG or JPEG")
    return path


def utf8_console() -> None:
    """Machine-readable CLI output must stay UTF-8 even on legacy Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

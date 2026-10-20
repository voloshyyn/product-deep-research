# Word report structure

Use the request language; default Russian. Write findings as atomic claims with classification, date, confidence and linked evidence. The generator derives factual prose from these claims and never writes unreferenced narrative facts.

1. Cover: product identity, industry, requested market, research date, depth, language, exact product URL, variant and run/product IDs. Cover metadata describes the requested scope; availability/company facts belong in sourced findings.
2. Executive summary: selected claim IDs, including consequential limitations and hypotheses with labels.
3. Objectives, scope and methodology: objectives, methods actually used, geography, devices/states, competitor comparison group/URLs, access and test boundaries.
4. All 15 standard sections in `research-method.md`. Use findings, relevant structured values/tables, evidence and explicit gaps; never omit an inaccessible category.
5. Dedicated additional research sections, one per request criterion. Preserve the request text and its findings/limitations.
6. Journey testing: goal, actual status, ordered actions/URLs, supported observed outcomes and stop reasons. Planned actions remain distinguishable from executed actions.
7. Detailed UX findings: issue, page URL, Nielsen heuristics, 0–4 severity, rationale, impact, evidence, WCAG references if applicable and concrete solution.
8. Prioritized recommendations: P0–P3, actions, rationale and linked finding IDs; estimates remain hypotheses.
9. Evidence and verification: classification policy, exact evidence records, dates, locations, source references and captured screenshots.
10. Sources: exact clickable URLs, access dates/methods/results, publisher type and independence group.
11. Limitations: inaccessible information, partial findings, unresolved contradictions, untested states and evidence gaps.
12. Final conclusions: selected claim IDs only, preserving their statuses.

Typography: A4, generous margins, Calibri 11 pt, black heading hierarchy, consistent paragraph spacing, compact structured tables with light gray borders and repeated headers, page numbers after the cover. Screenshots are constrained by width and height. Long analysis stays in prose. Source URLs are rendered in full and hyperlinked. Screenshots and all substantive dataset fields remain available in the output JSON even when summarized in the report.

Review the generated Word file; rendering in a real Word/LibreOffice engine is the reliable layout check. Structural XML checks do not establish visual fidelity. If rendering is unavailable, state this. Do not ship template/scaffold claims as research results.

## Other languages

Russian and English labels are built in. For another language set `research.language` and provide translations for every key from `report_writer.LABELS['en']` plus every standard category key in `research_core.CATEGORIES` via the optional `labels` object. All finding text, method descriptions, objectives, custom sections and recommendations must also be written in that language. Status and identifier tokens intentionally remain stable English machine identifiers.

Label keys: `report, summary, scope, custom, journeys, issues, recommendations, verification, sources, limitations, conclusions, industry, market, date, method, depth, language, context, evidence, qualification, gap, value, none, status, claim, test, goal, severity, impact, solution, rationale, request, independence, access, classification, confidence, verified, screenshots, comparison, verification_note`, plus the 15 category keys in the schema.

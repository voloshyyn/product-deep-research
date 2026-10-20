# Dataset and workbook contract version 1.0

`research-schema.json` is a strict JSON Schema Draft 2020-12 contract. Unknown properties are errors. `validate_research.py` additionally validates evidence links, source access, dates, category/custom coverage, journey evidence and screenshot paths/files. Dates use `YYYY-MM-DD`; identifiers are case sensitive and unique within each collection. Null means no structured value, not zero. Arrays of references contain IDs, never citation prose. The CLI rejects duplicate JSON keys and NaN/Infinity.

## Data model

- `product`: name, exact reviewed identity URL, regional variant, industry and requested market. These identify the research subject and scope; they do not establish product availability or legal company facts. Put those in claims.
- `research`: unique run ID, date, language (required in stored data; initializer defaults to `ru`), depth, objective strings, procedural methodology, comparison group, competitor URLs and additional requirements `{id,title,request}`.
- `sources`: `{id,url,title,publisher_type,independence_group,access_status,accessed_on,access_method,access_detail}`. Publisher type is FIRST_PARTY/INDEPENDENT; access is ACCESSED/NOT_ACCESSIBLE. Methods are WEB/BROWSER/PLAYWRIGHT/DOCUMENT. `access_detail` describes actual retrieval or failed attempt, including tool/time/state if available. Syndicated sources share an independence group.
- `evidence`: `{id,source_id,kind,verified_on,detail,locator,screenshot}`. Kinds are FIRST_PARTY_STATEMENT, INDEPENDENT_CORROBORATION, DIRECT_OBSERVATION. `detail` captures what was actually established; `locator` identifies page section, tool interaction, state, viewport or selectors. Optional screenshot is null or an existing relative PNG/JPEG path under input-adjacent `screenshots/`. Evidence cannot use an inaccessible source.
- `claims`: atomic `{id,category,title,statement,kind,status,confidence,verified_on,source_ids,evidence_ids,qualification,gap_reason,custom_requirement_id,facet,value,unit}`. The schema lists all category keys. Kind is FACT/COMPANY_CLAIM/OBSERVATION/INTERPRETATION; status is VERIFIED/PARTIALLY_VERIFIED/HYPOTHESIS/UNVERIFIED/NOT_ACCESSIBLE; confidence is HIGH/MEDIUM/LOW. `facet` is strength/weakness/opportunity/null. `value` is scalar or null, and `unit` carries currency/period/region where applicable. Use separate atomic claims for price conditions when they require separate evidence.
- `sections`: exactly one `{category,claim_ids,limitation}` per standard category. Every claim must appear in its own section. A category without findings needs an explicit limitation.
- `custom_sections`: exactly one `{requirement_id,claim_ids,limitation}` per additional requirement. Custom claims have `category="custom"` and a matching `custom_requirement_id`; standard claims have null. Keep the original request in the requirement record even when decomposing it.
- `journeys`: `{id,title,goal,status,steps,evidence_ids,limitation}`; steps are `{action,url,outcome_claim_ids}`. Status TESTED/PARTIAL/NOT_TESTED. Planned actions may have no outcomes; TESTED steps require supported observations and actual browser evidence. Partial/untested journeys require a stop reason. Record adjusted journey counts in overall limitations.
- `ux_issues`: `{id,title,claim_id,page_url,heuristics,severity,severity_rationale,impact,recommendation,priority,wcag}`. Heuristics are integers 1–10, severity an integer 0–4, priority P0–P3. All measured/observed assertions belong in the linked claim. Impact and rationale are analyst judgments, not extra unsourced metrics.
- `recommendations`: `{id,title,action,rationale,priority,claim_ids}`. These are proposals with linked factual premises, not predictions of guaranteed outcomes.
- `executive_summary`, `conclusions`: arrays of claim IDs. They cannot introduce factual prose outside the evidence ledger.
- `limitations`: explicit procedural, access, evidence and coverage limits. Do not hide factual findings here.
- `labels`: optional report translations. See `report-template.md` for keys.

Every claim date is no later than the run date; linked evidence cannot postdate its claim; source access cannot postdate its evidence. The validator checks structure and provenance consistency, not whether a human or model truthfully described a visit or whether evidence semantically entails the statement. Review source text, independence, screenshots and claim scope before export. Direct observation of a displayed statement does not establish its underlying truth.

Explicit gaps produce warnings and can be exported as gaps. `--strict-gaps` rejects them. Missing evidence on a supposedly confirmed claim is always an error. Downgrade unsupported findings and document missing evidence. The unresearched initializer is a scaffold, not a completed report.

## Stable identity and history

`product_id = prd_ + sha256(normalized_url + newline + normalized_regional_variant)[:24]`.
Normalize scheme to https for identity, lowercase/IDNA the host, remove a leading `www.`, default ports, fragments, trailing path slashes and known tracking query parameters (`utm_*`, gclid, fbclid, msclkid, dclid, mc_cid, mc_eid). Sort retained query parameters. Preserve path case, locale paths/subdomains, non-default ports and meaningful query parameters. This is syntactic identity normalization, not redirect discovery. Review canonical URLs first; unrelated domains and genuinely distinct offerings must never be merged merely because branding matches.

Researching another target market does not itself change product ID. A regional offering on the same URL can use `regional_variant`. Name or industry changes keep the product ID, but new runs can have a different output directory. Existing run retries use the recorded original paths. New run IDs are required for revised research. No product record is destructively updated; each row represents one finding in one historical product/run snapshot.

## Excel worksheet schemas

The executable source of truth is `scripts/research_core.py:SCHEMAS`; schema mismatches cause a refusal, never a migration or truncation. Column names below are literal and consistent. All worksheets begin with **C**:

`record_id, product_id, product_name, product_url, regional_variant, industry, market, run_id, research_date, comparison_group`

Claim columns **F**:

`claim_id, category, title, claim_kind, facet, confirmed_fact, qualified_claim, hypothesis, gap, value, unit, qualification, verification_status, confidence, verified_on, evidence_ids, source_urls`

| Worksheet | Columns after C | Row unit |
| --- | --- | --- |
| Overview | F | Overview, positioning or trust claim or coverage gap |
| Audience & JTBD | F | Audience/JTBD or customer problem claim or gap |
| Features & Services | F | Functionality or product/service claim or gap |
| Pricing & Business | F | Pricing or business model claim or gap |
| Marketing | F | Marketing claim or gap |
| UX & UI | F | Journey, UX, UI or accessibility claim or gap |
| Strengths & Weaknesses | F | Strength/weakness/general synthesis claim or gap |
| Opportunities | F | A claim with facet opportunity, retaining its original category and epistemic status |
| Custom Research | requirement_id, requirement_title, user_request, then F | One custom claim or explicit custom coverage gap |
| Sources | source_id, source_url, source_title, publisher_type, independence_group, access_status, accessed_on, access_method, access_detail, evidence_id, evidence_kind, verified_on, evidence_detail, locator, screenshot, verification_status, confidence, linked_claim_ids | One evidence record or source without evidence |
| UX Issues | issue_id, claim_id, title, page_url, heuristics, severity, severity_rationale, impact, recommendation, priority, wcag, verification_status, confidence, evidence_ids, source_urls | One UX issue |
| Research History | canonical_url, dataset_sha256, report_path, dataset_path, language, depth, objectives, methodology, limitations, claim_count, gap_count, verification_status, evidence_ids, source_urls | One immutable product/run |

Types: research_date/accessed_on/verified_on are real Excel dates (`yyyy-mm-dd`); severity and counts are integers; confirmed numerical `value` is numeric; boolean values remain boolean; IDs and classifications are text. Linked ID lists use `; `, URL lists use newlines. Each source has its own clickable `source_url` row; for multi-URL claim cells, the hyperlink opens the first URL and all URLs remain readable. Report and dataset paths are absolute local paths. All source URLs remain exact, independently of normalized identity.

`confirmed_fact` is populated only for VERIFIED FACT/OBSERVATION. `qualified_claim` holds VERIFIED COMPANY_CLAIM or PARTIALLY_VERIFIED statements; partials require an explicit qualification and company claims retain kind. `hypothesis` holds HYPOTHESIS only. `gap` holds UNVERIFIED/NOT_ACCESSIBLE statements and reasons. `value`/`unit` are populated only for VERIFIED FACT/OBSERVATION; qualified and hypothetical structured values remain labeled in JSON/report and never enter confirmed value fields. Scope identity fields are metadata on all rows.

Sources is a provenance ledger, so it retains unsupported/inaccessible source records with their access status. For sources/history aggregating several statuses, `verification_status` and confidence are sorted semicolon-separated sets, not a new evidence classification. UX Issues always includes the linked claim status, so a hypothesis is never disguised as an observed defect.

Record IDs hash product ID, run ID, worksheet and claim/issue/evidence identifier. Retries add no rows. The history key is `(product_id, run_id)`; collisions with changed datasets are errors. Every JSON field remains in immutable `research.json`, including journeys and recommendations that are summarized through linked claims/issues in the workbook. All 12 worksheet schemas exist even when a worksheet has no relevant records.

Claims always appear in their category worksheet. A strength/weakness/opportunity facet also appears in its corresponding synthesis worksheet when different, using the same claim ID and a worksheet-specific record ID. These intentional cross-references do not create additional product/run history entries.

## Publication and recovery

Exports validate the complete batch, acquire an exclusive `.export.lock`, stage all files and workbook, read back the workbook, back up an existing database, publish new run directories, then atomically replace `competitors.xlsx`. Ordinary failures roll back new run directories and keep the prior workbook. A process termination or power failure can leave a stale lock, stage directory or unindexed run directory; there is no distributed transaction or crash-proof filesystem guarantee. Confirm the process has stopped before removing a lock. Preserve unindexed directories for inspection; restore a database from `.backups/` if necessary or use new run IDs. Do not delete or overwrite historical reports to silence an error.

Keep storage on a local filesystem; cross-machine/network-filesystem locking is not supported. Close the workbook in Excel during export. Backups are never pruned automatically. Existing hand-edited workbook schemas are not migrated. Cells longer than 32767 characters fail rather than silently losing detail; split claims or reduce redundant source lists while retaining all evidence in JSON.

# Product Deep Research

A cross-industry Codex Skill combining live evidence collection, product and competitor analysis, browser journey testing, and deterministic Word/Excel exports. Research is performed by Codex with available web/browser tools. Python validates provenance and generates local artifacts; it does not crawl websites or verify the truth of natural language automatically.

## Install

The folder `product-deep-research/` is the complete Skill package. Follow the [official Codex Skills documentation](https://developers.openai.com/codex/skills/) for skill discovery and supported locations (checked 2026-10-20). It includes YAML-frontmatter `SKILL.md`, optional UI metadata, scripts and references. User skills can live under `~/.agents/skills/`; symlinked skill folders are supported.

Python 3.11+ is required. From this workspace on Windows:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r product-deep-research/requirements.txt
.\.venv\Scripts\python.exe product-deep-research/scripts/install_skill.py
```

The installer copies this package to `~/.agents/skills/product-deep-research/` and **refuses any existing target**, including a symlink. It does not modify Codex configuration or other skills. A Python virtual environment is not copied; retain this environment or create a dedicated one and give Codex its interpreter path. No activation is necessary when calling the interpreter by full path. No hardcoded username or machine path is used.

On macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r product-deep-research/requirements.txt
.venv/bin/python product-deep-research/scripts/install_skill.py
```

Alternatively link the package into `~/.agents/skills/product-deep-research` using an OS directory symlink or Windows junction, after checking that the target does not already exist. The copy installer is the portable default and needs no symlink privilege.

Restart Codex if it has not picked up the new Skill. Open `/skills` in Codex CLI or type `$product-deep-research` in the IDE and confirm the name appears. Run a small real research request and verify reported output paths. `install_skill.py --check` checks the installed manifest only; it does not prove host discovery or test a restarted IDE. Check for duplicate skill names and disabled `[[skills.config]]` entries if discovery fails. This project never silently changes those settings.

For an actual discovery check with the installed Codex CLI, without starting a model turn:

```powershell
.\.venv\Scripts\python.exe product-deep-research/scripts/check_codex_discovery.py --expected-path "$env:USERPROFILE/.agents/skills/product-deep-research" --repeat 2
```

This uses the CLI's experimental app-server `skills/list` method in two fresh processes. It verifies that the expected Skill is discovered and enabled across process restarts; it does not restart or test your existing IDE session. Future Codex protocol changes may require updating this optional diagnostic.

## Configuration

Production dependencies: `python-docx`, `openpyxl`, `jsonschema` (bounded major versions in `requirements.txt`). Development dependencies add `pytest` and `PyYAML`. Install them with `-r product-deep-research/requirements-dev.txt`. No API key is needed by the scripts. Codex itself needs its normal authenticated access and available research tools.

Use live web research tools for current information. Playwright is optional and preferred when installed/permitted; the Skill uses available browser tools otherwise. With no browser, record interaction/accessibility checks as untested. Browser installation, network permissions and access to blocked/authenticated products depend on the host. Word/LibreOffice rendering is optional for layout QA, not a runtime export dependency.

Default research language is Russian when none is specified; the language of the user's research request takes precedence. Russian/English report labels are built in; other languages use a complete `labels` translation dictionary. See [report-template.md](references/report-template.md).

Default storage:

```text
~/product-research/
  competitors.xlsx
  .backups/competitors-<timestamp>-<id>.xlsx
  <industry>/<product-slug>-<stable-id-prefix>/<YYYY-MM-DD_run-id>/
    report.docx
    research.json
    manifest.json
    screenshots/
```

`~` is the actual Python user's home. The product folder includes an ID suffix to avoid collisions between similarly named products. Configure `PRODUCT_RESEARCH_HOME` or pass `--storage-root`; the command-line argument wins. Windows example:

```powershell
$env:PRODUCT_RESEARCH_HOME = Join-Path $env:USERPROFILE 'product-research'
```

Research outside Codex's writable workspace can need host permission or launching Codex with that directory explicitly allowed. Respect the host sandbox; use a workspace `--storage-root` if needed. Creating this Skill and testing it does not initialize a production database.

## Invoke in Codex

```text
$product-deep-research Исследуй https://example.com для рынка Украины. Глубина deep. Дополнительно проверь локализацию и условия отмены.

$product-deep-research Research Product Name for the UK in English. Compare with https://competitor.example. Include enterprise onboarding and API access as additional criteria.

$product-deep-research Исследуй https://example.com, стандартная глубина. Отчет на русском. Используй Python из <полный путь к .venv>.
```

These are invocation examples, not researched products. All 15 categories remain mandatory at every depth. Every additional requirement gets its own section and structured records. Competitors receive separate datasets and full standard coverage linked by comparison group.

## Research and export workflow

1. Resolve product identity/region; capture scope, checklist and all custom criteria.
2. Visit public sources and record exact URLs, dates, access results and atomic evidence. Inspect primary pricing/terms, features, policies and independent material where relevant.
3. Test 3–5 appropriate journeys with actual browser tools when available; capture significant screenshots and stop before unauthorized side effects.
4. Classify observations, facts, attributed company claims, partial findings, hypotheses and gaps; analyze Nielsen heuristics, UI, accessibility and concrete recommendations.
5. Cross-check material claims and contradictions; validate JSON, export Word and historical Excel, inspect deliverables and return paths and limitations.

Create an evidence-free scaffold (never present it as completed research):

```powershell
.\.venv\Scripts\python.exe product-deep-research/scripts/init_research.py --name 'Product' --url 'https://example.com' --industry 'education' --market 'UK' --language en --requirement 'Inspect API access' --output .work/research.json
```

Collect evidence and replace scaffold gaps using [schema-guide.md](references/schema-guide.md) and the strict [JSON Schema](references/research-schema.json). Put screenshots under `.work/screenshots/` and reference relative paths.

```powershell
.\.venv\Scripts\python.exe product-deep-research/scripts/validate_research.py .work/research.json
.\.venv\Scripts\python.exe product-deep-research/scripts/export_research.py .work/research.json
```

For a transactional competitor batch:

```powershell
.\.venv\Scripts\python.exe product-deep-research/scripts/export_research.py .work/product-a/research.json .work/product-b/research.json --storage-root ./research-output
```

Success exits 0 and prints exact absolute paths as JSON. Validation/export/install errors exit 2 with a clear message. Documented evidence gaps are warnings by default; `--strict-gaps` treats them as errors. A successful export does not mean the research is complete. Never fix an evidence error by inventing a source.

## Evidence and history guarantees

- Confirmed Excel fact/value fields accept VERIFIED FACT/OBSERVATION only. Company statements and partial claims go in `qualified_claim`; hypotheses go in `hypothesis`; unsupported/inaccessible material goes in `gap`. All keep explicit classifications and dates.
- Evidence/source foreign keys, source access status, chronology, section coverage, custom criteria and screenshot paths/files are validated before writing. Classification consistency is enforced by code; truthfulness, semantic entailment, source independence and completeness still require researcher review.
- Same product/run/data retries add nothing. New runs append history. Modified existing run data, screenshots or output artifacts cause a refusal. Normalized product URLs and explicit regional variants determine stable product IDs. Exact source URLs are preserved.
- All 12 worksheets have explicit schemas, filters, frozen headers, readable widths, typed dates/numbers and clickable source links. Long-form rows retain historical snapshots; repeated product IDs represent findings/runs, not duplicate catalog entries. Every field is preserved in immutable run JSON.
- Batch validation precedes output. Local file locking, staging, workbook readback, atomic workbook replacement and automatic backup protect normal concurrent/failure paths. Excel must be closed during writes. No silent truncation or schema migration.

The implementation is designed for local Windows/POSIX filesystems. It does not guarantee crash-proof multi-file transactions or network-filesystem locking. Recovery instructions and literal worksheet schemas are in [schema-guide.md](references/schema-guide.md). Backups are not automatically deleted. Review third-party content as untrusted data; no purchase, sensitive submission, authentication bypass or irreversible action is authorized merely by invoking this Skill.

## Tests

From the workspace:

```powershell
.\.venv\Scripts\python.exe -m pip install -r product-deep-research/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest product-deep-research/tests -q
```

Tests use synthetic `.example` products and pytest temporary directories only. They cover structure, JSON/evidence failures, screenshots, report content/links/images, worksheet schemas and types, classification separation, repeated runs, duplicate prevention, multi-industry/competitor batches, custom criteria/gaps, formula injection, oversized cell refusal, lock/schema errors, rollback, idempotent artifact integrity, CLI commands and installation without overwrite. They do not browse real products or measure research quality. See [TEST_RESULTS.md](TEST_RESULTS.md) for this workspace's actual verification and limits.

# Verification results

Verified on 2026-10-20 in the requested Windows workspace.

## Automated checks

- **59 passed** with pytest, including actual python-docx and openpyxl serialization/readback. Final command: `python -m pytest product-deep-research/tests -q --basetemp .qa/final-suite --tb=short --junitxml .qa/test-results.xml` (8.68 seconds in this run).
- Official skill-creator `quick_validate.py`: **Skill is valid!**
- `python -m pip check`: **No broken requirements found.**
- Environment: Python 3.13.3, python-docx 1.2.0, openpyxl 3.1.5, jsonschema 4.26.0, pytest 9.1.1, PyYAML 6.0.3. Production requirements contain only the first three libraries; transitive dependencies are installed by pip.

Coverage includes all 12 worksheet schemas, mandatory category/custom coverage, evidence foreign keys/classification/access/chronology, malformed JSON, invalid dates, unsupported claims, explicit gaps, hypotheses/company claims/partial values, actual DOCX paragraphs/links/images/page-number fields, date/number types, formula injection, long-cell refusal, repeat-run idempotence, history preservation, multiple industries and competitor products, configuration precedence, screenshot integrity, manifest integrity, locking, schema mismatch and publication-failure rollback. Installer tests execute the relocated exporter and confirm existing destinations are refused.

All fixtures explicitly identify themselves as synthetic. Tests and diagnostic exports were stored under workspace `.qa/` or pytest temporary directories. No synthetic data were exported to `~/product-research/competitors.xlsx`; no existing user Skill was modified.

## Codex discovery

Codex CLI **0.163.0** successfully discovered an installed test copy at `.qa/discovery/.agents/skills/product-deep-research/SKILL.md`, with `scope=repo` and `enabled=true`, in **two fresh app-server processes** using `skills/list` with `forceReload=true`. No model turn was started. The copy installer and live discovery diagnostic succeeded.

This verifies the package's actual local discovery across server process restarts. Global user installation at `~/.agents/skills/product-deep-research/` is prepared through the installer; it was not performed. The user's running VS Code/Codex session was not restarted. After global installation, run `check_codex_discovery.py --expected-path <installed-directory> --repeat 2` and confirm the Skill in `/skills` or the IDE selector.

## Limits of verification

- No real product research, live Playwright journey test or external purchase/submission was performed. Web/browser research is an agent workflow, not a Python crawler. Evidence integrity checks do not prove the semantic truth or independence of natural language evidence.
- Word files were generated and reopened successfully, including embedded screenshots, source hyperlinks, styles and page-number fields. **Visual page layout was not verified.** The bundled `render_docx.py` was attempted and failed because LibreOffice `soffice.exe` is unavailable. A hidden automation attempt with the installed Microsoft Word did not complete; only the identified QA helper and its new Word process were stopped. No rendered page images were available for visual review.
- Python 3.11+ and POSIX compatibility follow the implementation/API choices; execution here was on Windows/Python 3.13 only. Future package releases within declared version ranges were not tested.
- Failure rollback was tested by injecting an atomic workbook publication error. Power failure/process-kill crash recovery and network-filesystem locking are not guaranteed; see `references/schema-guide.md`.
- The optional discovery script uses an experimental local Codex app-server protocol and may need maintenance when Codex changes.

The release package includes source, tests, instructions and these recorded verification limits. Generated `.qa/` files and the local virtual environment are excluded from the installable package.

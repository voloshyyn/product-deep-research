# Product Deep Research for Codex

A reusable Codex Skill for evidence-based research of digital products, websites, marketplaces and SaaS platforms across industries. It combines 15 standard research categories with every additional user requirement and exports Word reports, structured JSON, screenshot evidence and a historical Excel competitor database.

The installable Skill lives in [`product-deep-research/`](product-deep-research/). Read the [installation and usage guide](product-deep-research/README.md), [Skill instructions](product-deep-research/SKILL.md), and [verification results and limitations](product-deep-research/TEST_RESULTS.md).

## Install from this repository

Requires Python 3.11+. From the repository root on Windows:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r product-deep-research/requirements.txt
.\.venv\Scripts\python.exe product-deep-research/scripts/install_skill.py
```

On macOS or Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r product-deep-research/requirements.txt
.venv/bin/python product-deep-research/scripts/install_skill.py
```

The installer targets `~/.agents/skills/product-deep-research/` and refuses existing destinations. Restart Codex if necessary and select `$product-deep-research`.

```text
$product-deep-research Research https://example.com for the UK market in English. Include API access and onboarding as additional criteria.
```

Research uses available Codex web/browser tools; the Python scripts validate and export collected evidence. Default output storage is `~/product-research/`. No real research data, credentials or local virtual environment are included in this repository.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r product-deep-research/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest product-deep-research/tests -q
```

The recorded verification run passed 59 tests. Tests use isolated synthetic fixtures; visual Word layout and live product/browser research were not verified.

The [ZIP package](dist/product-deep-research.zip) contains the installable Skill source, references and tests.

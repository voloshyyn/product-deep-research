import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from fixtures import dataset, write_dataset
from install_skill import install

ROOT = Path(__file__).resolve().parents[1]


def test_skill_structure_and_local_references():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata = yaml.safe_load(text.split("---", 2)[1])
    assert metadata["name"] == ROOT.name == "product-deep-research"
    assert isinstance(metadata["description"], str) and metadata["description"]
    assert "TODO" not in text
    import re
    for target in re.findall(r"\]\((references/[^)]+)\)", text):
        assert (ROOT / target).is_file()
    config = yaml.safe_load((ROOT / "agents/openai.yaml").read_text())
    assert "$product-deep-research" in config["interface"]["default_prompt"]
    assert len(config["interface"]["short_description"]) <= 64


def test_installer_copy_relocates_and_never_overwrites(tmp_path):
    destination = tmp_path / "home" / ".agents" / "skills" / "product-deep-research"
    installed = install(destination)
    assert (installed / "scripts/export_research.py").is_file()
    with pytest.raises(ValueError, match="already exists"):
        install(destination)
    source = write_dataset(tmp_path / "in", dataset())
    command = subprocess.run([sys.executable, str(installed / "scripts/export_research.py"), str(source),
        "--storage-root", str(tmp_path / "out")], capture_output=True, text=True, encoding="utf-8")
    assert command.returncode == 0, command.stderr
    assert Path(json.loads(command.stdout)["database"]).is_file()


def test_cli_init_validate_export_and_errors(tmp_path):
    output = tmp_path / "scaffold.json"
    command = [sys.executable, str(ROOT / "scripts/init_research.py"), "--name", "Demo", "--url", "https://demo.example", "--output", str(output)]
    assert subprocess.run(command, capture_output=True).returncode == 0
    assert subprocess.run(command, capture_output=True).returncode == 2
    source = write_dataset(tmp_path / "in", dataset())
    check = subprocess.run([sys.executable, str(ROOT / "scripts/validate_research.py"), str(source)], capture_output=True, text=True, encoding="utf-8")
    assert check.returncode == 0 and json.loads(check.stdout)["valid"]
    bad = tmp_path / "bad.json"
    bad.write_text('{"incomplete": true}')
    check = subprocess.run([sys.executable, str(ROOT / "scripts/export_research.py"), str(bad), "--storage-root", str(tmp_path / "out")], capture_output=True, text=True, encoding="utf-8")
    assert check.returncode == 2 and "validation failed" in check.stderr
    assert not (tmp_path / "out").exists()

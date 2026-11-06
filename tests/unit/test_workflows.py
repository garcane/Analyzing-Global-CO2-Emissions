"""GitHub only reports an invalid workflow file after it is pushed, as a failed run on every push.
Parse every file under .github/ locally with a real YAML parser, and check the structure we rely on.
"""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
FILES = sorted((ROOT / ".github").rglob("*.yml"))
WORKFLOWS = [f for f in FILES if f.parent.name == "workflows"]


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_yaml_parses(path):
    assert isinstance(yaml.safe_load(path.read_text(encoding="utf-8")), dict)


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_workflow_structure(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    # YAML 1.1 reads the key `on` as boolean True; GitHub accepts it either way.
    assert "on" in doc or True in doc, "workflow has no trigger"
    assert doc.get("permissions"), "workflow must set explicit (least-privilege) permissions"
    for name, job in doc["jobs"].items():
        assert job.get("runs-on"), f"job {name} has no runs-on"
        assert job.get("timeout-minutes"), f"job {name} has no timeout"
        for step in job["steps"]:
            assert "uses" in step or "run" in step, f"job {name}: step without uses/run"


def test_snowflake_workflow_is_manual_only_and_gated():
    doc = yaml.safe_load((ROOT / ".github/workflows/dbt-snowflake.yml").read_text(encoding="utf-8"))
    triggers = doc.get("on", doc.get(True))
    assert set(triggers) == {"workflow_dispatch"}, "the Snowflake workflow must not run on push or pull_request"
    assert doc["jobs"]["build"]["environment"] == "snowflake-trial"
    # The drop step must run even if the build fails, and must use the guarded macro.
    drops = [s for s in doc["jobs"]["build"]["steps"] if "drop_ci_schemas" in str(s.get("run", ""))]
    assert drops and "always()" in str(drops[0].get("if"))
    # ...and no secret may be handed to the cleanup or build step directly: credentials come from the prepare step.
    for step in doc["jobs"]["build"]["steps"]:
        if step.get("id") == "dbt" or "drop_ci_schemas" in str(step.get("run", "")):
            assert "secrets." not in str(step.get("env", {}))


def test_ci_workflow_uses_no_secrets():
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "${{ secrets." not in text, "the always-on CI must not depend on secrets or Snowflake"

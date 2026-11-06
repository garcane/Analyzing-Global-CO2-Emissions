"""Offline repository checks that run in CI: no secrets in tracked files, profile uses env_var() only.

Findings report the file and the rule, never the matched text, so a failing run cannot leak the secret.
"""

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".sql", ".toml", ".txt", ".example", ".cfg", ".ini", ".sh"}

# (rule name, regex)
RULES = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("base64 private key body", re.compile(r"MIIE[vwo][A-Za-z0-9+/]{40,}")),
    ("uuid-shaped API key assignment", re.compile(r"(?i)api[_-]?key\s*[=:]\s*['\"]?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-")),
    ("API key in query string", re.compile(r"(?i)[?&]api_key=[0-9a-f]{8}")),
    ("hard-coded password", re.compile(r"(?i)\bpassword\s*=\s*[\"'][^\"'<>{$ ]{4,}[\"']")),
]


def tracked_files() -> list[Path]:
    """Committed files PLUS new files not yet committed (but not git-ignored), so a secret is caught
    before it is ever committed, and local runs cover work in progress. Ignored files (.env, keys) are
    excluded by design; they are never committed."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return [ROOT / p for p in out]


def test_scan_covers_uncommitted_and_workflow_files():
    names = {p.relative_to(ROOT).as_posix() for p in tracked_files()}
    assert "dbt/profiles.yml" in names and ".github/workflows/ci.yml" in names
    assert ".env" not in names  # ignored on purpose


def scan_text(text: str) -> list[str]:
    return [name for name, rx in RULES if rx.search(text)]


def test_rules_detect_what_they_should():
    # Synthetic values only: guards against the scanner silently matching nothing.
    assert scan_text("-----BEGIN PRIVATE KEY-----") == ["private key block"]
    assert scan_text("EMBER_API_KEY=12345678-1234-1234-1234-123456789abc")
    assert scan_text("https://x/y?api_key=deadbeef&a=1")
    assert scan_text('password = "hunter22"')
    assert scan_text("MIIEv" + "A" * 50)
    assert scan_text("EMBER_API_KEY=") == []
    assert scan_text("# no password variable on purpose") == []
    assert scan_text("MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA" + "A" * 50) == []  # PUBLIC key is fine


def test_no_secrets_in_tracked_files():
    findings = []
    for path in tracked_files():
        if path == SELF or not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if path.name == "uv.lock":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings += [f"{path.relative_to(ROOT).as_posix()}: {rule}" for rule in scan_text(text)]
    assert not findings, "possible secrets in tracked files (values not shown):\n" + "\n".join(findings)


def test_secret_files_are_not_tracked():
    bad = [
        p.relative_to(ROOT).as_posix()
        for p in tracked_files()
        if p.name == ".env" or p.suffix in {".p8", ".pem", ".key", ".ppk"} or p.name == "snowflake_connector.py"
    ]
    assert not bad, f"secret-bearing files are tracked: {bad}"


def test_dbt_profile_only_uses_env_vars_for_connection_values():
    profile = (ROOT / "dbt" / "profiles.yml").read_text(encoding="utf-8")
    for key in ("account", "user", "role", "private_key_path"):
        for line in profile.splitlines():
            if re.match(rf"\s+{key}:", line):
                assert "env_var(" in line, f"dbt/profiles.yml: '{key}' must come from env_var()"
    assert "password" not in profile.lower()


@pytest.mark.parametrize("name", [".env", ".p8"])
def test_gitignore_covers_secret_patterns(name):
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert name in gitignore or f"*{name}" in gitignore

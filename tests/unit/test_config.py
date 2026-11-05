import pytest

from ingestion.config import ConfigError, SnowflakeSettings

BASE = {"account": "ORG-ACC", "user": "U", "role": "GEI_LOADER", "warehouse": "GEI_WH", "database": "RAW"}


@pytest.mark.parametrize("role", ["ACCOUNTADMIN", "accountadmin", "SECURITYADMIN", "SYSADMIN", "ORGADMIN"])
@pytest.mark.parametrize("auth", ["keypair", "externalbrowser"])
def test_admin_roles_are_refused(role, auth):
    with pytest.raises(ConfigError, match="Refusing to run as"):
        SnowflakeSettings(**{**BASE, "role": role}, authenticator=auth, private_key_path=None)


def test_unknown_authenticator_rejected():
    with pytest.raises(ConfigError, match="AUTHENTICATOR"):
        SnowflakeSettings(**BASE, authenticator="password")


def test_keypair_requires_key_path():
    with pytest.raises(ConfigError, match="PRIVATE_KEY_PATH"):
        SnowflakeSettings(**BASE, authenticator="keypair")


def test_browser_mode_needs_no_key_and_sends_no_key():
    s = SnowflakeSettings(**BASE, authenticator="externalbrowser")
    p = s.connection_params()
    assert p["authenticator"] == "externalbrowser"
    assert "private_key" not in p and "password" not in p
    assert p["role"] == "GEI_LOADER"


def test_from_env_defaults_to_keypair_and_ignores_blank_values(monkeypatch, tmp_path):
    monkeypatch.setattr("ingestion.config.load_dotenv", lambda *_a, **_k: None)
    for k, v in {"SNOWFLAKE_ACCOUNT": "A-B", "SNOWFLAKE_USER": "U", "SNOWFLAKE_ROLE": "",
                 "SNOWFLAKE_PRIVATE_KEY_PATH": str(tmp_path / "k.p8"), "SNOWFLAKE_AUTHENTICATOR": ""}.items():
        monkeypatch.setenv(k, v)
    s = SnowflakeSettings.from_env()
    assert (s.authenticator, s.role, s.warehouse, s.database) == ("keypair", "GEI_LOADER", "GEI_WH", "RAW")


def test_from_env_browser_mode_ignores_key_path(monkeypatch):
    monkeypatch.setattr("ingestion.config.load_dotenv", lambda *_a, **_k: None)
    for k, v in {"SNOWFLAKE_ACCOUNT": "A-B", "SNOWFLAKE_USER": "U", "SNOWFLAKE_AUTHENTICATOR": "ExternalBrowser",
                 "SNOWFLAKE_PRIVATE_KEY_PATH": "C:/does/not/exist.p8"}.items():
        monkeypatch.setenv(k, v)
    s = SnowflakeSettings.from_env()
    assert s.authenticator == "externalbrowser" and s.private_key_path is None

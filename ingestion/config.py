"""Configuration from environment variables (optionally a local .env). No secrets in code."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
API_DIR = DATA_DIR / "api"


class ConfigError(RuntimeError):
    pass


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"Environment variable {name} is not set (see .env.example)")
    return value


KEYPAIR = "keypair"            # service user + private key: the only mode for CI/automation
EXTERNALBROWSER = "externalbrowser"  # interactive SSO login in a browser: local development only
AUTHENTICATORS = (KEYPAIR, EXTERNALBROWSER)

# Routine ingestion/dbt must never run as an administrator, whichever way you authenticate.
FORBIDDEN_ROLES = {"ACCOUNTADMIN", "SECURITYADMIN", "ORGADMIN", "USERADMIN", "SYSADMIN"}


@dataclass(frozen=True)
class SnowflakeSettings:
    account: str
    user: str
    role: str
    warehouse: str
    database: str
    authenticator: str = KEYPAIR
    private_key_path: Path | None = None
    private_key_passphrase: str | None = None

    def __post_init__(self) -> None:
        if self.authenticator not in AUTHENTICATORS:
            raise ConfigError(
                f"SNOWFLAKE_AUTHENTICATOR must be one of {AUTHENTICATORS}, got {self.authenticator!r}"
            )
        if self.role.upper() in FORBIDDEN_ROLES:
            raise ConfigError(
                f"Refusing to run as {self.role}: use a least-privilege role such as GEI_LOADER "
                "(administrator roles are only for running infra/snowflake_setup.sql in Snowsight)"
            )
        if self.authenticator == KEYPAIR and self.private_key_path is None:
            raise ConfigError("SNOWFLAKE_PRIVATE_KEY_PATH is required when SNOWFLAKE_AUTHENTICATOR=keypair")

    @classmethod
    def from_env(cls) -> SnowflakeSettings:
        load_dotenv(REPO_ROOT / ".env")
        authenticator = os.environ.get("SNOWFLAKE_AUTHENTICATOR", "").strip().lower() or KEYPAIR
        key_path = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "").strip()
        return cls(
            account=_require("SNOWFLAKE_ACCOUNT"),
            user=_require("SNOWFLAKE_USER"),
            role=os.environ.get("SNOWFLAKE_ROLE", "").strip() or "GEI_LOADER",
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "").strip() or "GEI_WH",
            # Landing database for this project. A stale SNOWFLAKE_DATABASE is deliberately ignored so a
            # leftover value can never send a load into another project's database.
            database=os.environ.get("GEI_RAW_DATABASE", "").strip() or "GEI_RAW",
            authenticator=authenticator,
            private_key_path=Path(key_path) if key_path and authenticator == KEYPAIR else None,
            private_key_passphrase=os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE") or None,
        )

    def connection_params(self) -> dict:
        """Arguments for snowflake.connector.connect(), for the configured authentication mode."""
        params: dict = {
            "account": self.account,
            "user": self.user,
            "role": self.role,
            "warehouse": self.warehouse,
            "database": self.database,
            "session_parameters": {"QUERY_TAG": "gei-ingestion"},
        }
        if self.authenticator == KEYPAIR:
            params["private_key"] = self.private_key_der()
        else:
            params["authenticator"] = EXTERNALBROWSER
            # Ask the connector to cache the SSO token so you are not prompted on every run.
            # [Verify] whether the account allows ID-token caching (ALLOW_ID_TOKEN).
            params["client_store_temporary_credential"] = True
        return params

    def private_key_der(self) -> bytes:
        """Load the PEM private key and return unencrypted PKCS8 DER bytes for the connector."""
        from cryptography.hazmat.primitives import serialization

        passphrase = self.private_key_passphrase.encode() if self.private_key_passphrase else None
        key = serialization.load_pem_private_key(self.private_key_path.read_bytes(), passphrase)
        return key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )


def ember_api_key() -> str:
    load_dotenv(REPO_ROOT / ".env")
    return _require("EMBER_API_KEY")


def mask_secret(text: str, secret: str) -> str:
    """Remove a secret (and its URL-encoded form) from text before logging or raising."""
    if not secret:
        return text
    masked = text.replace(secret, "***")
    return re.sub(r"(api_key=)[^&\s'\"]+", r"\1***", masked)

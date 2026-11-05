# Snowflake setup and first load

Steps 1–3 are yours (they need admin rights and your secrets). Keys and `.env` must never be committed; `.gitignore` already excludes `.env`, `*.p8`, `*.pem`, `*.key`.

## 1. Create a key pair for each service user (outside the repo)

Git Bash ships with `openssl`:

```bash
mkdir -p ~/.snowflake && cd ~/.snowflake
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out gei_loader.p8 -nocrypt
openssl rsa -in gei_loader.p8 -pubout -out gei_loader.pub
# repeat with gei_transformer for dbt (Phase 3)
```

Use a passphrase (`-v2 aes256` instead of `-nocrypt`) if you prefer; then set `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE`.
Paste the **contents of the `.pub` file without the BEGIN/END lines** into `RSA_PUBLIC_KEY` in the SQL below.

## 2. Run `infra/snowflake_setup.sql`

Read it first. Replace `<LOADER_PUBLIC_KEY>` / `<TRANSFORMER_PUBLIC_KEY>`, adjust `CREDIT_QUOTA`, then run it section by section in a Snowflake worksheet.

## 3. Fill in `.env` (copy from `.env.example`)

```
SNOWFLAKE_ACCOUNT=<your account identifier, e.g. orgname-accountname>
SNOWFLAKE_USER=GEI_LOADER_SVC
SNOWFLAKE_PRIVATE_KEY_PATH=C:/Users/<you>/.snowflake/gei_loader.p8
SNOWFLAKE_ROLE=GEI_LOADER
EMBER_API_KEY=<the key from Ember's email>
```

### Alternative for local development: browser login

Instead of the service-user key, you can sign in through the browser as yourself:

1. Run the optional section 7 in `infra/snowflake_setup.sql` (grants `GEI_LOADER` to your login).
2. In `.env`: `SNOWFLAKE_AUTHENTICATOR=externalbrowser`, `SNOWFLAKE_USER=<your login name>`, `SNOWFLAKE_ROLE=GEI_LOADER`, and leave `SNOWFLAKE_PRIVATE_KEY_PATH` empty.

A browser window opens on each new connection (the loader asks the connector to cache the token; whether your account allows that is not verified). This mode cannot run in GitHub Actions. The loader refuses `ACCOUNTADMIN`, `SYSADMIN`, `SECURITYADMIN`, `USERADMIN` and `ORGADMIN` in both modes.

## 4. Load

```bash
uv run python -m ingestion.cli owid_co2_csv --dry-run      # validate only
uv run python -m ingestion.cli owid_co2_csv                # load
uv run python -m ingestion.cli ember_yearly_csv
uv run python -m ingestion.cli ember_api --dry-run         # fetch + validate the API extract only
uv run python -m ingestion.cli ember_api
```

## 5. Check (acceptance for Phase 2)

```sql
SELECT SOURCE_NAME, STATUS, EXPECTED_ROWS, LOADED_ROWS, FINISHED_AT_UTC FROM RAW.META.INGESTION_LOG ORDER BY STARTED_AT_UTC DESC;
SELECT COUNT(*) FROM RAW.EMBER.GENERATION_YEARLY;   -- 104256 for the current file
SELECT COUNT(*) FROM RAW.OWID.CO2;                  -- 50191 for the current file
```

Run each load twice: the second run must report `skipped` and add no rows. `ember_api --dry-run` makes one request per endpoint with no entity filter; the API's behaviour for such unfiltered requests (response size/time) has not been tested yet.

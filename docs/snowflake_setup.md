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

## 2. Run `infra/snowflake_setup.sql` (v2)

Read it first. v2 creates the project's own databases `GEI_RAW` and `GEI_ANALYTICS`, scopes all grants to them, and **revokes** the broader v1 grants on the shared `RAW` / `ANALYTICS` databases (section 5). It does not drop or change any tutorial object, and it leaves removing the old v1 schemas (`RAW.EMBER`, `RAW.OWID`, `RAW.META`, `ANALYTICS.STAGING|INTERMEDIATE|MARTS`) to you, after the reload into `GEI_RAW` is verified.

Replace `<LOADER_PUBLIC_KEY>` / `<TRANSFORMER_PUBLIC_KEY>` only if the service users do not exist yet (section 6 is a no-op for existing users), adjust `CREDIT_QUOTA`, then run it in a Snowflake workspace as `ACCOUNTADMIN`. Afterwards `SHOW GRANTS TO ROLE GEI_TRANSFORMER` must list nothing on `RAW`, `ANALYTICS`, `JAFFLE_SHOP`, `STRIPE` or `DBT_GARCANE`.

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
SELECT SOURCE_NAME, STATUS, EXPECTED_ROWS, LOADED_ROWS, FINISHED_AT_UTC FROM GEI_RAW.META.INGESTION_LOG ORDER BY STARTED_AT_UTC DESC;
SELECT COUNT(*) FROM GEI_RAW.EMBER.GENERATION_YEARLY;   -- 104256 for the current file
SELECT COUNT(*) FROM GEI_RAW.OWID.CO2;                  -- 50191 for the current file
```

## 6. dbt (Phase 3)

dbt signs in as `GEI_TRANSFORMER_SVC` (`DBT_SNOWFLAKE_*` variables in `.env`). Always run it through the wrapper, which loads `.env` and the OS certificate store:

```bash
uv run python dbt/run_dbt.py debug                 # connection check
uv run python dbt/run_dbt.py seed
uv run python dbt/run_dbt.py build                 # dev target: dbt_<DBT_DEV_SUFFIX>_staging / _intermediate / _marts
uv run python dbt/run_dbt.py build --target prod   # exact STAGING / INTERMEDIATE / MARTS (what Power BI reads)
uv run python dbt/run_dbt.py source freshness
```

Run each load twice: the second run must report `skipped` and add no rows. `ember_api --dry-run` makes one request per endpoint with no entity filter; the API's behaviour for such unfiltered requests (response size/time) has not been tested yet.

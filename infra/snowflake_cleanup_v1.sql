-- Remove the v1 copies of this project from the shared RAW / ANALYTICS databases.
-- Run manually in Snowsight, step by step. Drops are destructive: read the checks first.
--
-- What v1 created (2026-11-04): RAW.EMBER, RAW.OWID, RAW.META (our first loads) and the empty schemas
-- ANALYTICS.STAGING, ANALYTICS.INTERMEDIATE, ANALYTICS.MARTS. The project now lives in GEI_RAW / GEI_ANALYTICS.
-- NEVER touched here: JAFFLE_SHOP, STRIPE, PUBLIC, DBT_GARCANE and the RAW / ANALYTICS databases themselves.
-- Undo: UNDROP SCHEMA <name>; works within Time Travel retention ([Verify] your account's retention).
-- The data is also reproducible: python -m ingestion.cli <source> loads it again from the repo files.

USE ROLE SYSADMIN;

----------------------------------------------------------------------
-- STEP 1. CHECKS (read-only). Look at the results before running anything below.
----------------------------------------------------------------------
-- 1a. When was each schema created, and by whom? v1 objects were created 2026-11-04 around 18:51 by SYSADMIN.
--     A schema created earlier than that, or by someone else, is NOT ours: do not drop it.
SELECT 'RAW' AS db, schema_name, schema_owner, created, last_altered, comment
FROM RAW.INFORMATION_SCHEMA.SCHEMATA
WHERE schema_name <> 'INFORMATION_SCHEMA'
UNION ALL
SELECT 'ANALYTICS', schema_name, schema_owner, created, last_altered, comment
FROM ANALYTICS.INFORMATION_SCHEMA.SCHEMATA
WHERE schema_name <> 'INFORMATION_SCHEMA'
ORDER BY 1, 2;

-- 1b. What is inside the v1 schemas? Expected:
--     RAW.EMBER : 4 tables (GENERATION_YEARLY, API_GENERATION_YEARLY, API_DEMAND_YEARLY, API_EMISSIONS_YEARLY)
--     RAW.OWID  : 1 table  (CO2)
--     RAW.META  : INGESTION_LOG (table), LATEST_SUCCESSFUL_LOAD (view), INGEST_STAGE (stage)
--     ANALYTICS.STAGING / INTERMEDIATE / MARTS : nothing
SELECT table_schema, table_name, table_type
FROM RAW.INFORMATION_SCHEMA.TABLES
WHERE table_schema IN ('EMBER', 'OWID', 'META')
ORDER BY 1, 2;

SELECT table_schema, table_name, table_type
FROM ANALYTICS.INFORMATION_SCHEMA.TABLES
WHERE table_schema IN ('STAGING', 'INTERMEDIATE', 'MARTS')
ORDER BY 1, 2;

-- 1c. The new copies exist and hold the data (should be 104256 / 50191).
SELECT COUNT(*) AS gei_raw_ember_rows FROM GEI_RAW.EMBER.GENERATION_YEARLY;
SELECT COUNT(*) AS gei_raw_owid_rows  FROM GEI_RAW.OWID.CO2;

----------------------------------------------------------------------
-- STEP 2. DROP the empty v1 schemas in ANALYTICS.
-- RESTRICT makes each statement FAIL if the schema contains anything, so tutorial work cannot be
-- deleted by accident. If a statement fails, stop: that schema is not empty and is not ours.
----------------------------------------------------------------------
-- DROP SCHEMA IF EXISTS ANALYTICS.STAGING      RESTRICT;
-- DROP SCHEMA IF EXISTS ANALYTICS.INTERMEDIATE RESTRICT;
-- DROP SCHEMA IF EXISTS ANALYTICS.MARTS        RESTRICT;

----------------------------------------------------------------------
-- STEP 3. DROP the v1 copies in RAW. Only after 1b showed exactly the objects listed above.
-- (These schemas contain our v1 tables, so they are dropped with CASCADE.)
----------------------------------------------------------------------
-- DROP SCHEMA IF EXISTS RAW.EMBER CASCADE;
-- DROP SCHEMA IF EXISTS RAW.OWID  CASCADE;
-- DROP SCHEMA IF EXISTS RAW.META  CASCADE;

----------------------------------------------------------------------
-- STEP 4. Check the result: only tutorial schemas should remain.
----------------------------------------------------------------------
-- SHOW SCHEMAS IN DATABASE RAW;        -- expect: INFORMATION_SCHEMA, JAFFLE_SHOP, PUBLIC, STRIPE
-- SHOW SCHEMAS IN DATABASE ANALYTICS;  -- expect: DBT_GARCANE (+ INFORMATION_SCHEMA, PUBLIC)

# config

[`config.toml`](config.toml) lists every setting the loaders, the build and the DAGs read, at its
default. It holds no secrets: those go in `config/.env` (copy [`.env.example`](.env.example), which
names each one), and the settings refuse a secret written in `config.toml`.

## How a value is chosen

Highest first: an environment variable, then `config/.env`, then `config.toml`, then the default in
[`pipelines/config.py`](../pipelines/config.py). Each key's environment name is its section and key
joined by an underscore, in capitals: `[warehouse] path` is `WAREHOUSE_PATH`. A nested table is one
setting: `[ai_ops.apps]` is `AI_OPS_APPS`, a JSON object in the environment. A test
(`tests/test_config.py`) keeps `config.toml` equal to the defaults in code.

dbt reads the same warehouse: `python -m pipelines dbt ...` sets `WAREHOUSE_PATH` and the Databricks
variables from these settings before it starts dbt, and `dbt/profiles.yml` reads them.

## Every setting

| Setting | Default | What it does |
| --- | --- | --- |
| `[warehouse] destination` | `duckdb` | Where dlt loads: `duckdb`, or `databricks` with the three Databricks secrets |
| `[warehouse] path` | `data/generated/warehouse.duckdb` | The DuckDB file dlt loads and dbt builds in |
| `[warehouse] state` | `data/generated/dlt` | dlt's pipeline state |
| `[dbt] project` | `dbt` | The dbt project, which also holds `profiles.yml` |
| `[dbt] target` | `dev` | `dev` builds in DuckDB, `prod` in Databricks |
| `[dbt] threads` | `4` | Models dbt builds at once |
| `[github] api`, `raw`, `owner` | GitHub's | Where the apps' repositories are listed and read |
| `[github] timeout_s` | `30.0` | How long one request may take |
| `[ai_ops] dataset` | `raw_ai_ops` | The schema the apps' results load into |
| `[ai_ops] results` | `data/evals/results` | The folder every app commits its run files to |
| `[ai_ops] prices_repo`, `prices_path` | `utils`, `llm/kds/llm/pricing.json` | Where the workbench's price list is |
| `[ai_ops] prices_commits` | utils v0.6.1 | Every utils commit that holds a version of the price list |
| `[ai_ops.apps]` | each app's main after the Nov 8 merges | Each app's repository and the full commit SHA its results are read at |
| `[eeoc_stats] dataset` | `raw_eeoc_stats` | The schema the EEOC's statistics load into |
| `[eeoc_stats] url`, `timeout_s` | Table E1a, `60.0` | Where the EEOC publishes the receipts table, and how long the download may take |
| `[databricks] catalog` | `kds` | The Unity Catalog catalog every schema lives in |
| `[files] encoding` | `utf-8` | Every file read or written |
| `[log] dir`, `level` | `logs`, `INFO` | Where `kds.logs` writes one JSON line per event, and from what level |

## Secrets

| Variable | Needed for |
| --- | --- |
| `GITHUB_TOKEN` | Optional: a higher rate limit on GitHub's API. Workflows use their own token |
| `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH`, `DATABRICKS_TOKEN` | Loading into Databricks, and the dbt `prod` target |
| `POSTGRES_PASSWORD` | `make up`: Airflow's local metadata database |

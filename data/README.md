# data

Nothing here is committed. `generated/` is ignored, and every file in it is rebuilt by a load:

| Path | What it holds |
| --- | --- |
| `generated/warehouse.duckdb` | The warehouse: the raw schemas dlt loads and every schema dbt builds |
| `generated/dlt/` | dlt's state for each pipeline: what each load did, and the schemas it inferred |
| `generated/airflow/` | Airflow's home for `make dags-test`: its SQLite database and task logs |
| `generated/requirements-audit.txt` | The locked list `make audit` checks |

The data the warehouse holds is the apps' own committed results, read at the commits in
`config/config.toml`. Every charge, client, matter, question and person in those results is made up
by the apps' generators.

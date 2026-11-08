# dags

Three Airflow 3 DAGs. Every task runs one command in the project's locked environment,
`uv run --no-sync python -m pipelines ...`, at the repository root, so a DAG holds no logic of its
own and the same command runs from a laptop, CI or a hosted Airflow.

| DAG | Schedule | Tasks |
| --- | --- | --- |
| `load_ai_ops` | Daily, 06:17 UTC | `load_results`: the apps' results at their pins and the price list; updates the `raw_ai_ops` asset |
| `load_eeoc_stats` | The 3rd of each month, 07:43 UTC | `load_receipts`: the EEOC's receipts table; updates the `raw_eeoc_stats` asset |
| `build_warehouse` | When either asset is updated | `freshness`, then `build` (`dbt build`), then `docs` |

Every task retries twice with backoff and has a 30-minute limit; every DAG runs one at a time and
never backfills. [`defaults.py`](defaults.py) holds what they share, and `.airflowignore` keeps
Airflow from parsing it as a DAG. Airflow puts this folder on the path, so the DAGs import it as
`defaults`; `make dags-test` and `compose.yaml` do the same through `PYTHONPATH`.

`tests/test_dags.py` parses the folder with Airflow's own DagBag and checks each DAG's settings and
commands. `make dags-test` runs `load_ai_ops` and `build_warehouse` end to end through Airflow.

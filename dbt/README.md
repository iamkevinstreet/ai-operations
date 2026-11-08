# dbt

One dbt project, built in DuckDB (`dev`, CI) or Databricks (`prod`). Run it through
`python -m pipelines dbt <command>`, which points `profiles.yml` at the warehouse the loaders used;
`make build` and `make docs` do.

| Folder | Layer | Built as |
| --- | --- | --- |
| `models/staging/` | One view per raw table, `stg_<source>__<table>`: renamed and cast, nothing joined | Views in `staging` |
| `models/intermediate/` | The apps' two run formats lined up to one grain | Views in `intermediate` |
| `models/ai_ops/` | The published AI operations mart: `dim_`, `fct_` and `rpt_` tables, each with an enforced contract, in the `ai_ops` group, public | Tables in `ai_ops` |
| `seeds/` | `apps` and `published_metrics`, the reference tables | Tables in `reference` |
| `macros/` | The schema names, a surrogate key, a sorted list each adapter writes its own way, and two generic tests | |
| `tests/` | The list-price check on every call, and a trace for every case of a traced run | |

The repository's code standard allows three folders below the root, so the published marts sit in
a folder per domain directly under `models/`, beside the staging and intermediate layers.

Every mart's YAML gives its grain and columns with their types; the unit tests in
`models/ai_ops/_ai_ops__unit_tests.yml` check the window and format logic on hand-written rows.
Anonymous usage reporting and the version check are off in `dbt_project.yml`.

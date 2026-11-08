# Changelog

Every release, newest first. Versions follow [Semantic Versioning](https://semver.org/).

## v0.1.0 (Nov 8, 2026)

The first release: the AI operations load and mart, the schedules and the infrastructure.

### Added

- `python -m pipelines load ai-ops`: a dlt source that reads every app's committed run files and
  traces at pinned commits, and the workbench's price list, into `raw_ai_ops`, merging on each
  table's key. Pins are full commit SHAs only. Spans keep their ids, times, status and GenAI
  numbers, never prompt, answer or tool text.
- The raw contract: one Pydantic model per raw table, which dlt reads for the columns, and models of
  the apps' file formats, so a changed format fails the load.
- `python -m pipelines load eeoc-stats`: the EEOC's charge receipts by basis, read from the XLSX by
  its shape. Not yet run on the EEOC's real file; CI runs it without failing the build until it is.
- The dbt project: 11 staging views, 4 intermediate views and 15 `ai_ops` marts with enforced
  contracts, 2 seeds, 4 unit tests, 92 data tests, and source freshness. `fct_run_metrics` rebuilds
  every published summary figure from case rows, and the build fails on any that differs beyond
  rounding; a singular test holds every recorded call cost to the list price.
- Three Airflow 3 DAGs: two loads that update assets, and a build scheduled on either asset.
- Terraform for AWS (a private, versioned, TLS-only bucket and a CI role assumed through GitHub's
  OIDC token) and for Databricks (catalog, schemas, a landing volume, groups and grants).
- `compose.yaml` and a Dockerfile for Airflow and its Postgres on one machine.
- CI: lint, strict types, the code standard, 34 offline tests, the audit, the DAG tests, the real
  loads and build, Terraform's format and validation, and the Compose file's. A daily workflow runs
  the DAGs with `airflow dags test`, and copies the warehouse to S3 when an AWS role is set.

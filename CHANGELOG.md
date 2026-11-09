# Changelog

Every release, newest first. Versions follow [Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- **Dependency updates land by themselves.** Dependabot groups each week's updates into one pull
  request per kind (Actions, Python), and the `dependency-updates` workflow lands them every
  weekday: it applies the oldest open one to `main` as an ordinary commit, refreshes the dates in the
  headers it changes, runs the whole of CI on that commit, and moves `main` to it only when every
  check passes. One whose checks fail is labelled "needs a person" and waits; one that changes a
  workflow waits for the `DEPENDENCY_UPDATES_TOKEN` secret.

## v0.2.0 (Nov 9, 2026)

Renamed from data-platform: this repository is now the AI operations project, one use case among
the projects, and the platform it runs on is a repository of its own.

### Changed

- The project is `ai-operations`, the dbt project and profile `ai_operations`, and the local
  Airflow's folder `/opt/ai-operations`, read from `AI_OPERATIONS_HOME`.
- The daily copy to the lake writes under `ai-operations/`, so each project deploying onto the
  platform keeps to its own prefix.

### Moved

- The Terraform for AWS and Databricks and the bootstrap, with their tests, to
  [data-platform-aws-databricks](https://github.com/iamkevinstreet/data-platform-aws-databricks),
  whose CI role trusts this repository by name and id. The Compose and Dockerfile tests stay here,
  in `tests/test_compose.py`.
- The EEOC's national charge receipts loader, its DAG and its tests, out of this project: they
  belong to the EEOC charge warehouse, in eeoc-charge-intake, and are restored there from this
  repository's history at 8c6b715.

### Tests

- 27 offline tests; openpyxl and python-hcl2 are no longer dependencies.

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
  its shape. It first read the EEOC's real file in CI on Nov 8, 338 rows over FY1997 to FY2025;
  until its figures are checked against the EEOC's published totals, CI reports a failure there
  without failing the build.
- The dbt project: 11 staging views, 4 intermediate views and 15 `ai_ops` marts with enforced
  contracts, 2 seeds, 4 unit tests, 92 data tests, and source freshness. `fct_run_metrics` rebuilds
  every published summary figure from case rows, and the build fails on any that differs beyond
  rounding; a singular test holds every recorded call cost to the list price.
- Three Airflow 3 DAGs: two loads that update assets, and a build scheduled on either asset.
- Terraform for AWS (a private, versioned, TLS-only bucket and a CI role assumed through GitHub's
  OIDC token) and for Databricks (catalog, schemas, a landing volume, groups and grants).
- `compose.yaml` and a Dockerfile for Airflow and its Postgres on one machine.
- `infra/bootstrap.sh`: the AWS side built once from CloudShell, with Terraform's state in a private,
  versioned bucket of its own.
- On Databricks, the catalog comes from the `DATABRICKS_CATALOG` variable, and a pasted
  `https://` host is accepted; tags are sorted the way each adapter can sort them.
- CI: lint, strict types, the code standard, 34 offline tests, the audit, the DAG tests, the real
  loads and build, Terraform's format and validation, and the Compose file's. A daily workflow runs
  the DAGs with `airflow dags test`, copies the warehouse to S3 once `AWS_REGION` is set, and runs
  the loads and models on Databricks once `DATABRICKS_CATALOG` is set.
- Whatever names an account (the AWS role and bucket, the Databricks host, HTTP path and token) is
  a repository secret, so the public workflow logs mask it, the AWS account id included.
- The CI role trusts GitHub's OIDC subject in the form every repository made after July 15, 2026
  carries, owner and repository by name and by id. The first sign-in from main, Nov 9, was refused
  under the old, name-only subject; a refused sign-in now prints the claims it offered.
- First runs on Databricks, Nov 8: the load and all 128 models, seeds and tests pass on the Free
  Edition's 2X-Small SQL warehouse. The first build broke one contract: `percentile_disc` returns a
  double there, so the run percentiles are cast to bigint, which loses nothing.

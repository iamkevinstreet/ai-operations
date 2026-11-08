# Security

## Reporting a vulnerability

Please report it privately, never in a public issue:

- **Preferred:** GitHub's private vulnerability reporting (the repository's **Security** tab, then
  **Report a vulnerability**).
- **Otherwise:** email info@kevindstreet.com with "Security" in the subject.

Include what you found, how to reproduce it, and what an attacker could do with it. You will get an
answer within 3 business days. A confirmed issue is fixed within 30 days, sooner when severe, and you
are credited in the advisory unless you would rather not be.

## Scope

In scope: the loaders in `pipelines/`, the dbt project, the DAGs, the Terraform, the Compose file and
the workflows in `.github/`, and above all any way to load text the warehouse should never hold, to
widen the CI role's rights, or to make a load read something other than its pin.

Out of scope: the apps' own repositories, GitHub, AWS and Databricks themselves, the made-up data
the apps' results describe, and findings that need a compromised developer machine.

## How this repository is protected

| Risk | Control |
| --- | --- |
| Text in the warehouse | Spans keep ids, times, status and GenAI numbers only; prompts, answers, retrieval queries, tool arguments and values read are never parsed into a row; a test checks no raw column could hold text |
| A load that reads something new without review | Each app is read at a full commit SHA; a branch name or a short SHA is refused; each run row records its commit and git blob |
| A format change that loads half a row | The raw contract refuses a field it does not know, and the format models refuse a missing one |
| A wrong number reaching a mart | Enforced contracts on every mart, unit tests, data tests, the reconciliation of every published figure and the list-price check on every call, all in `dbt build`, which stops a failed model's children |
| A key for AWS that could leak | None exists: workflows assume an IAM role through GitHub's OIDC token, trusted for one repository's main branch, for an hour at most; the role can list, read and add objects in one bucket, never delete |
| A public bucket | Every public-access switch on, objects owned by the bucket, TLS required, versioning on; a test checks the Terraform |
| A committed secret | gitleaks before every commit and over the whole history in CI; secrets live only in `config/.env` and GitHub secrets, and the settings loader refuses one in `config/config.toml` |
| Usage data leaving the machine | dlt's and dbt's anonymous usage reporting are off, in code and in `dbt_project.yml` |
| A vulnerable dependency | A lockfile with hashes, `pip-audit` over every group in CI, Dependabot every week. Two oauthlib advisories are waived, in the Databricks group only, until dbt-databricks allows a newer SQL connector; the Makefile says why |
| A tampered Action or tool | Actions pinned to commit SHAs; the gitleaks download checked against its published SHA-256; Docker bases and Terraform providers pinned |
| A local service reachable by others | Airflow's UI binds to 127.0.0.1 only; its Postgres has no published port |

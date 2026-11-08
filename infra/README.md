# infra

Two Terraform roots, each with its own state, so the cloud account and the workspace can be built
and torn down apart. CI checks the format and validates both against their providers' schemas on
every push; neither has been applied yet.

## aws

The lake bucket and the role GitHub Actions assumes to write to it.

- The bucket: every public-access switch on, objects owned by the bucket, AES-256 encryption,
  versioning, replaced versions expired after 30 days, and TLS required by its policy.
- GitHub's OIDC provider (or the account's existing one, with `create_oidc_provider = false`).
- `data-platform-ci`: trusted for `repo:iamkevinstreet/data-platform:ref:refs/heads/main` only, for an
  hour at most, allowed to list the bucket and to read and add objects, never to delete them.

The first time, from AWS CloudShell, signed in to the account (no key is created or stored).
Replace `YOUR-LAKE-NAME` with a name of your own, 3 to 55 lowercase letters, numbers and hyphens,
unique across AWS; the script refuses the placeholder and any name another account holds:

```bash
git clone https://github.com/iamkevinstreet/data-platform && cd data-platform
BUCKET=YOUR-LAKE-NAME bash infra/bootstrap.sh
```

[`bootstrap.sh`](bootstrap.sh) installs Terraform if CloudShell lacks it, makes a private, versioned
state bucket named after the lake bucket, writes the root's `backend.hcl` (ignored by git), and
applies the root in CloudShell's region. It prints what to set in the repository's Actions settings:
the secrets `AWS_ROLE_ARN` and `LAKE_BUCKET`, which name the account and stay masked in the public
logs, and the variable `AWS_REGION`, which turns the copy on. From then on the daily workflow copies
the warehouse and its docs to the bucket. Run it again with the same name to apply a change; it
changes only what differs.

## databricks

Every Unity Catalog object the warehouse needs, so a deleted Free Edition workspace can be rebuilt
from here: the catalog, one schema per layer, a managed `exports` volume for files to load, and
three groups with their grants. Loaders write the raw schemas; builders read raw and own every
model; readers see the published marts only. Grants are authoritative, so the catalog's are set
only on a catalog this root created.

```bash
cd infra/databricks
export DATABRICKS_HOST=... DATABRICKS_TOKEN=...   # a workspace token; workspace APIs only
terraform init -backend-config=backend.hcl       # the state bucket, key databricks/terraform.tfstate
terraform apply                                  # or -var create_catalog=false -var catalog=workspace
```

This root is optional for the first loads: dlt and dbt create their own schemas in the catalog the
`DATABRICKS_CATALOG` variable names, such as the Free Edition's own `workspace`. Setting that
variable turns the daily workflow's Databricks job on. It reads three secrets: `DATABRICKS_HOST`
(the SQL warehouse's server hostname, without `https://`), `DATABRICKS_HTTP_PATH` (its HTTP path,
also this root's output `sql_warehouse_http_path`) and `DATABRICKS_TOKEN`, a personal access token
scoped to `sql`, `files` and `unity-catalog`.

## Not yet known

These depend on what the Databricks Free Edition allows, and are checked on the first apply:
whether a workspace token may create a catalog and groups, whether Unity Catalog grants and managed
volumes are open to it, and how long the dbt build takes on its 2X-Small SQL warehouse.

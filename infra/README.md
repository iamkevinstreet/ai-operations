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

```bash
cd infra/aws
terraform init -backend-config=backend.hcl   # bucket, key and region of the state; never committed
terraform apply -var bucket_name=<a globally unique name>
```

Then set the repository variables `AWS_ROLE_ARN` (the `ci_role_arn` output), `LAKE_BUCKET` and
`AWS_REGION`, and the daily workflow copies the warehouse and its docs to the bucket.

## databricks

Every Unity Catalog object the warehouse needs, so a deleted Free Edition workspace can be rebuilt
from here: the catalog, one schema per layer, a managed `exports` volume for files to load, and
three groups with their grants. Loaders write the raw schemas; builders read raw and own every
model; readers see the published marts only. Grants are authoritative, so the catalog's are set
only on a catalog this root created.

```bash
cd infra/databricks
export DATABRICKS_HOST=... DATABRICKS_TOKEN=...   # a workspace token; workspace APIs only
terraform init -backend-config=backend.hcl
terraform apply                                  # or -var create_catalog=false -var catalog=workspace
```

The output `sql_warehouse_http_path` is `DATABRICKS_HTTP_PATH` for dbt and dlt.

## Not yet known

These depend on what the Databricks Free Edition allows, and are checked on the first apply:
whether a workspace token may create a catalog and groups, whether Unity Catalog grants and managed
volumes are open to it, and how long the dbt build takes on its 2X-Small SQL warehouse.

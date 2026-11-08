# Author:            Kevin Street
# Created on:        2026-11-08
# Last modified on:  2026-11-08
#
# What dbt and dlt need to connect: the SQL warehouse's HTTP path, which
# goes in DATABRICKS_HTTP_PATH, and the catalog.

output "sql_warehouse_http_path" {
  description = "The HTTP path of the SQL warehouse; set it as DATABRICKS_HTTP_PATH."
  value       = data.databricks_sql_warehouse.dbt.odbc_params[0].path
}

output "catalog" {
  description = "The catalog every schema lives in."
  value       = var.catalog
}

# Author:            Kevin Street
# Created on:        2026-11-08
# Last modified on:  2026-11-09
#
# What changes between accounts: the region, the bucket's name, and the
# one repository and branch whose workflows may assume the CI role, by
# name and by GitHub's numeric ids.

variable "region" {
  description = "The AWS region the bucket and role live in."
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "The bucket's name; bucket names are global, so it is set per account."
  type        = string
}

variable "github_repository" {
  description = "The owner/name of the only repository whose workflows may assume the role."
  type        = string
  default     = "iamkevinstreet/data-platform"
}

variable "github_owner_id" {
  description = "The repository owner's numeric GitHub id, part of the OIDC subject."
  type        = number
  default     = 747156
}

variable "github_repository_id" {
  description = "The repository's numeric GitHub id, part of the OIDC subject."
  type        = number
  default     = 1450000844
}

variable "github_ref" {
  description = "The only branch whose workflows may assume the role."
  type        = string
  default     = "refs/heads/main"
}

variable "create_oidc_provider" {
  description = "Whether to create GitHub's OIDC provider; false when the account already has it."
  type        = bool
  default     = true
}

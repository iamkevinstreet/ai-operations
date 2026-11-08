#!/usr/bin/env bash
########################################################################
#                                                                      #
#                          infra/bootstrap.sh                          #
#                                                                      #
########################################################################
# Author:            Kevin Street
# Created on:        2026-11-08
# Last modified on:  2026-11-08
#
# Builds the AWS side once, from AWS CloudShell, signed in as the
# account's owner: a private, versioned state bucket, then the aws root
# (the lake bucket and the CI role) with its state in that bucket. Safe
# to run again; it changes only what differs.
#
#   BUCKET=<a globally unique name> bash infra/bootstrap.sh
#
# Then set three repository variables from what it prints: AWS_ROLE_ARN,
# LAKE_BUCKET and AWS_REGION. No key is created, printed or stored.

set -euo pipefail

: "${BUCKET:?set BUCKET to a globally unique name for the lake bucket}"
REGION="${AWS_REGION:-us-east-1}"
STATE="${BUCKET}-tfstate"
ROOT="$(cd "$(dirname "$0")/aws" && pwd)"

# Terraform, from HashiCorp's own package repository, when CloudShell lacks it.
if ! command -v terraform >/dev/null 2>&1; then
  sudo dnf install -y dnf-plugins-core
  sudo dnf config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
  sudo dnf install -y terraform
fi

# The state bucket: created once, then kept private, versioned and encrypted.
if ! aws s3api head-bucket --bucket "${STATE}" 2>/dev/null; then
  if [ "${REGION}" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "${STATE}" --region "${REGION}"
  else
    aws s3api create-bucket --bucket "${STATE}" --region "${REGION}" \
      --create-bucket-configuration "LocationConstraint=${REGION}"
  fi
fi
aws s3api put-public-access-block --bucket "${STATE}" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-versioning --bucket "${STATE}" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "${STATE}" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# The aws root's backend, written beside it; git ignores backend.hcl.
cat > "${ROOT}/backend.hcl" <<EOF
bucket       = "${STATE}"
key          = "aws/terraform.tfstate"
region       = "${REGION}"
encrypt      = true
use_lockfile = true
EOF

terraform -chdir="${ROOT}" init -input=false -backend-config=backend.hcl
terraform -chdir="${ROOT}" apply -input=false -var "bucket_name=${BUCKET}" -var "region=${REGION}"

echo
echo "Set these as repository variables (Settings, Secrets and variables, Actions, Variables):"
echo "  AWS_ROLE_ARN = $(terraform -chdir="${ROOT}" output -raw ci_role_arn)"
echo "  LAKE_BUCKET  = $(terraform -chdir="${ROOT}" output -raw bucket_name)"
echo "  AWS_REGION   = ${REGION}"

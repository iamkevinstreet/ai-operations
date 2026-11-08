# Author:            Kevin Street
# Created on:        2026-11-08
# Last modified on:  2026-11-08
#
# What the workflows need from this root: the bucket and the role ARN,
# which go in the repository's variables, never in a file.

output "bucket_name" {
  description = "The lake bucket's name."
  value       = aws_s3_bucket.lake.bucket
}

output "ci_role_arn" {
  description = "The role the workflows assume; set it as the AWS_ROLE_ARN repository variable."
  value       = aws_iam_role.ci.arn
}

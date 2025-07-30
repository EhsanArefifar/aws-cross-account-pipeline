output "artifact_bucket_name" {
  description = "Name of the S3 bucket for artifacts"
  value       = aws_s3_bucket.artifacts.bucket
}

output "artifact_bucket_arn" {
  description = "ARN of the S3 bucket for artifacts"
  value       = aws_s3_bucket.artifacts.arn
}

output "kms_key_arn" {
  description = "ARN of the KMS key for artifact encryption"
  value       = aws_kms_key.artifact_encryption.arn
}

output "kms_key_id" {
  description = "ID of the KMS key for artifact encryption"
  value       = aws_kms_key.artifact_encryption.key_id
}

output "repository_clone_url" {
  description = "Clone URL of the CodeCommit repository"
  value       = aws_codecommit_repository.app_repo.clone_url_http
}

output "repository_name" {
  description = "Name of the CodeCommit repository"
  value       = aws_codecommit_repository.app_repo.repository_name
}

output "pipeline_name" {
  description = "Name of the CodePipeline"
  value       = aws_codepipeline.pipeline.name
}

output "pipeline_arn" {
  description = "ARN of the CodePipeline"
  value       = aws_codepipeline.pipeline.arn
}
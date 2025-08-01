terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.region
  profile = "prod"
}

variable "tooling_account_id" {
  type = string
}

variable "region" {
  type = string
}

variable "project_name" {
  type = string
}

# Phase 3: Deploy roles WITH policies
module "iam_roles" {
  source = "../../modules/iam-roles"
  
  tooling_account_id = var.tooling_account_id
  prod_account_id    = var.prod_account_id
  project_name       = var.project_name
  
  # Phase 3: Create policies with S3/KMS resources
  create_policies       = true
  artifact_bucket_name  = "cross-account-demo-artifacts-730335606929"
  artifact_bucket_arn   = "arn:aws:s3:::cross-account-demo-artifacts-730335606929"
  kms_key_arn          = "arn:aws:kms:us-east-1:730335606929:key/6324d244-f2e1-4b01-818a-38d25a7fdb44"
}

output "codepipeline_role_arn" {
  value = module.iam_roles.codepipeline_role_arn
}

output "cloudformation_role_arn" {
  value = module.iam_roles.cloudformation_role_arn
}

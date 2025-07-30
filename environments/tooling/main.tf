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
  profile = "tooling"
}

variable "tooling_account_id" {
  type = string
}

variable "prod_account_id" {
  type = string
}

variable "region" {
  type = string
}

variable "project_name" {
  type = string
}

# Read role ARNs from Phase 1 outputs
data "local_file" "prod_outputs" {
  filename = "../prod/outputs.json"
}

locals {
  prod_outputs = jsondecode(data.local_file.prod_outputs.content)
}

# Phase 2: Deploy pipeline infrastructure
module "pipeline" {
  source = "../../modules/pipeline"
  
  project_name      = var.project_name
  region           = var.region
  tooling_account_id = var.tooling_account_id
  prod_account_id   = var.prod_account_id
  
  # Use role ARNs from Phase 1
  codepipeline_role_arn    = local.prod_outputs.codepipeline_role_arn.value
  cloudformation_role_arn  = local.prod_outputs.cloudformation_role_arn.value
}

output "artifact_bucket_name" {
  value = module.pipeline.artifact_bucket_name
}

output "artifact_bucket_arn" {
  value = module.pipeline.artifact_bucket_arn
}

output "kms_key_arn" {
  value = module.pipeline.kms_key_arn
}

output "repository_clone_url" {
  value = module.pipeline.repository_clone_url
}

output "pipeline_name" {
  value = module.pipeline.pipeline_name
}
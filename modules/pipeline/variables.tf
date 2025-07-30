variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "tooling_account_id" {
  description = "Account ID of the tooling account"
  type        = string
}

variable "prod_account_id" {
  description = "Account ID of the production account"
  type        = string
}

variable "codepipeline_role_arn" {
  description = "ARN of the CodePipeline cross-account role in prod account"
  type        = string
}

variable "cloudformation_role_arn" {
  description = "ARN of the CloudFormation deployment role in prod account"
  type        = string
}
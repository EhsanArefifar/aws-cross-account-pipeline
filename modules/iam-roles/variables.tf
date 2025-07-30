variable "tooling_account_id" {
    description = "Account ID of the tooling account"
    type = string
}

variable "prod_account_id" {
    description = "Account ID of the tooling account"
    type = string
}


variable "project_name" {
    description = "Name of the project"
    type = string  
}

variable "artifact_bucket_name" {
    description = "ARN of the artifact bucket (provided after pipeline creation)"  
    type = string
    default = ""
}

variable "artifact_bucket_arn" {
  description = "ARN of the artifact bucket (provided after pipeline creation)"
  type        = string
  default     = ""
}

variable "kms_key_arn" {
    description = "ARN of the KMS key (provided after pipeline creation)"
    type = string
    default = ""
}

variable "create_policies" {
    description = "Whether to create policies (set to True in Phase 3)"
    type = bool
    default = false
}
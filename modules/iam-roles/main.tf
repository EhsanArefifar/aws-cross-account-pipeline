data "aws_caller_identity" "current" {}

resource "aws_iam_role" "codepipeline_cross_account" {
  name = "CodePipelineCrossAccountRole"

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          "AWS" : "arn:aws:iam::${var.tooling_account_id}:root" # Source Account Root User
        }
      },
    ]
  })

  tags = {
    Project = var.project_name
    Purpose = "CrossAccountDeployyment"
  }
}

resource "aws_iam_role" "cloudformation_deployment" {
  name = "CloudFormationDeploymentRole"

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          "Service" : "cloudformation.amazonaws.com"
        }
      },
    ]
  })

  tags = {
    Project = var.project_name
    Purpose = "CloudFormationDeployyment"
  }
}
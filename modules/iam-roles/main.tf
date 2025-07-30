# Role that CodePipeline will assume
resource "aws_iam_role" "codepipeline_cross_account" {
  name = "CodePipelineCrossAccountRole"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.tooling_account_id}:root"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  
  tags = {
    Project = var.project_name
    Purpose = "CrossAccountDeployment"
  }
}

# Role that CloudFormation will use
resource "aws_iam_role" "cloudformation_deployment" {
  name = "CloudFormationDeploymentRole"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudformation.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  
  tags = {
    Project = var.project_name
    Purpose = "CloudFormationDeployment"
  }
}

# Policies created in Phase 3
# CodePipeline Cross-Account Role Policy
resource "aws_iam_role_policy" "codepipeline_cross_account_policy" {
  count = var.create_policies ? 1 : 0
  name  = "CodePipelineCrossAccountPolicy"
  role  = aws_iam_role.codepipeline_cross_account.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject"
        ]
        Resource = "${var.artifact_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.artifact_bucket_arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = var.kms_key_arn
      },
      {
        Effect = "Allow"
        Action = [
          "cloudformation:CreateStack",
          "cloudformation:UpdateStack",
          "cloudformation:DeleteStack",
          "cloudformation:DescribeStacks",
          "cloudformation:DescribeStackEvents",
          "cloudformation:DescribeStackResources",
          "cloudformation:GetTemplate"
        ]
        Resource = "arn:aws:cloudformation:*:${var.prod_account_id}:stack/${var.project_name}-*/*"
      }
    ]
  })
}

# CloudFormation Deployment Role Policy
resource "aws_iam_role_policy" "cloudformation_deployment_policy" {
  count = var.create_policies ? 1 : 0
  name  = "CloudFormationDeploymentPolicy"
  role  = aws_iam_role.cloudformation_deployment.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${var.artifact_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = var.kms_key_arn
      },
      {
        Effect = "Allow"
        Action = [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:PassRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy"
        ]
        Resource = [
          "arn:aws:iam::${var.prod_account_id}:role/${var.project_name}-*",
          "arn:aws:iam::${var.prod_account_id}:role/lambda-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction",
          "lambda:DeleteFunction",
          "lambda:GetFunction",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:InvokeFunction",
          "lambda:TagResource",
          "lambda:UntagResource"
        ]
        Resource = "arn:aws:lambda:*:${var.prod_account_id}:function:${var.project_name}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "apigateway:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:DescribeLogGroups",
          "logs:PutRetentionPolicy"
        ]
        Resource = "arn:aws:logs:*:${var.prod_account_id}:log-group:/aws/lambda/${var.project_name}-*"
      }
    ]
  })
}
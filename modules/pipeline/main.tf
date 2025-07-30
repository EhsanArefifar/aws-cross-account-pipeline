data "aws_caller_identity" "current" {}

# KMS Key for cross-account encryption
resource "aws_kms_key" "artifact_encryption" {
  description = "KMS key for ${var.project_name} cross-account CI/CD artifacts"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.tooling_account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow use of the key for CodePipeline"
        Effect = "Allow"
        Principal = {
          Service = [
            "codepipeline.amazonaws.com",
            "codebuild.amazonaws.com"
          ]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow cross-account access from prod account"
        Effect = "Allow"
        Principal = {
          AWS = [
            var.codepipeline_role_arn,
            var.cloudformation_role_arn
          ]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = {
    Name    = "${var.project_name}-artifact-key"
    Project = var.project_name
  }
}

resource "aws_kms_alias" "artifact_encryption" {
  name          = "alias/${var.project_name}-artifact-key"
  target_key_id = aws_kms_key.artifact_encryption.key_id
}

# S3 Bucket for artifacts
resource "aws_s3_bucket" "artifacts" {
  bucket        = "${var.project_name}-artifacts-${var.tooling_account_id}"
  force_destroy = true
  
  tags = {
    Name    = "${var.project_name}-artifacts"
    Project = var.project_name
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.artifact_encryption.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_policy" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnSecureCommunications"
        Effect = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid    = "CrossAccountAccess"
        Effect = "Allow"
        Principal = {
          AWS = [
            var.codepipeline_role_arn,
            var.cloudformation_role_arn
          ]
        }
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.artifacts.arn}/*"
      },
      {
        Sid    = "CrossAccountListBucket"
        Effect = "Allow"
        Principal = {
          AWS = [
            var.codepipeline_role_arn,
            var.cloudformation_role_arn
          ]
        }
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.artifacts.arn
      }
    ]
  })
}

# CodeCommit Repository
resource "aws_codecommit_repository" "app_repo" {
  repository_name = "${var.project_name}-app"
  description     = "Repository for ${var.project_name} application code"
  
  tags = {
    Name    = "${var.project_name}-app"
    Project = var.project_name
  }
}

# CodeBuild Service Role
resource "aws_iam_role" "codebuild_role" {
  name = "${var.project_name}-codebuild-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "codebuild_policy" {
  name = "${var.project_name}-codebuild-policy"
  role = aws_iam_role.codebuild_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${var.tooling_account_id}:log-group:/aws/codebuild/${var.project_name}*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.artifacts.arn}/*"
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
        Resource = aws_kms_key.artifact_encryption.arn
      }
    ]
  })
}

# CodeBuild Project
resource "aws_codebuild_project" "build" {
  name         = "${var.project_name}-build"
  description  = "Build project for ${var.project_name}"
  service_role = aws_iam_role.codebuild_role.arn
  
  artifacts {
    type = "CODEPIPELINE"
  }
  
  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:3.0"
    type         = "LINUX_CONTAINER"
  }
  
  source {
    type = "CODEPIPELINE"
    buildspec = "buildspec.yml"
  }
  
  tags = {
    Project = var.project_name
  }
}

# CodePipeline Service Role
resource "aws_iam_role" "codepipeline_role" {
  name = "${var.project_name}-codepipeline-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codepipeline.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "codepipeline_policy" {
  name = "${var.project_name}-codepipeline-policy"
  role = aws_iam_role.codepipeline_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject",
          "s3:GetBucketVersioning"
        ]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "codecommit:CancelUploadArchive",
          "codecommit:GetBranch",
          "codecommit:GetCommit",
          "codecommit:GetRepository",
          "codecommit:ListBranches",
          "codecommit:ListRepositories"
        ]
        Resource = aws_codecommit_repository.app_repo.arn
      },
      {
        Effect = "Allow"
        Action = [
          "codebuild:BatchGetBuilds",
          "codebuild:StartBuild"
        ]
        Resource = aws_codebuild_project.build.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sts:AssumeRole"
        ]
        Resource = var.codepipeline_role_arn
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
        Resource = aws_kms_key.artifact_encryption.arn
      }
    ]
  })
}

# CodePipeline
resource "aws_codepipeline" "pipeline" {
  name     = "${var.project_name}-pipeline"
  role_arn = aws_iam_role.codepipeline_role.arn
  
  artifact_store {
    location = aws_s3_bucket.artifacts.bucket
    type     = "S3"
    
    encryption_key {
      id   = aws_kms_key.artifact_encryption.arn
      type = "KMS"
    }
  }
  
  stage {
    name = "Source"
    
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeCommit"
      version          = "1"
      output_artifacts = ["source_output"]
      
      configuration = {
        RepositoryName = aws_codecommit_repository.app_repo.repository_name
        BranchName     = "main"
      }
    }
  }
  
  stage {
    name = "Build"
    
    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"
      
      configuration = {
        ProjectName = aws_codebuild_project.build.name
      }
    }
  }
  
  stage {
    name = "Deploy"
    
    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "CloudFormation"
      input_artifacts = ["build_output"]
      version         = "1"
      region          = var.region
      
      configuration = {
        ActionMode    = "CREATE_UPDATE"
        StackName     = "${var.project_name}-app-stack"
        TemplatePath  = "build_output::template.yml"
        Capabilities  = "CAPABILITY_IAM"
        RoleArn       = var.cloudformation_role_arn
      }
      
      role_arn = var.codepipeline_role_arn
    }
  }
  
  tags = {
    Project = var.project_name
  }
}
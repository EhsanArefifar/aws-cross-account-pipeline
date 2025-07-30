## 🚀 Pushing a Local Project to GitHub

1. **Initialize Git**

   ```bash
   git init
   ```
   Sets up version control in your local project directory.
2. **Add Files**

   ```bash
   git add .
  ```
   Stages all files for the first commit.

3. **Commit Changes**

   ```bash
   git commit -m "Initial commit"
   ```
   Records the snapshot of your project.

4. **Create a GitHub Repo**

   * Go to [github.com](https://github.com)
   * Click **New repository**
   * **Do not** initialize with README, `.gitignore`, or license
   * Create the repo

5. **Add GitHub Remote**

   ```bash
   git remote add origin https://github.com/your-username/repo-name.git
   ```
   Links your local repo to the GitHub repository.

6. **Push to GitHub**

   ```bash
   git push -u origin main
   ```
   Pushes your code to the main branch on GitHub.

✅ Your project is now version-controlled and hosted on GitHub.
======================================================
aws configure list-profiles
aws s3 ls --profile my-special-profile
aws configure --profile my-special-profile # to config a special profile
aws configure list --profile my-special-profile

======================================================

## 🔐 Why We Need a KMS Key

**The Cross-Account Encryption Challenge:**

```
┌─────────────────┐         ┌─────────────────┐
│ Tooling Account │  ────>  │  Prod Account   │
│   (Pipeline)    │         │ (Deployment)    │
│                 │         │                 │
│ S3 Bucket with  │         │ Roles need to   │
│ encrypted       │         │ decrypt         │
│ artifacts       │         │ artifacts       │
└─────────────────┘         └─────────────────┘
```

- **S3 artifacts are encrypted** for security (buildspec files, CloudFormation templates, etc.)
- **Default S3 encryption** only works within the same account
- **Cross-account access** requires explicit KMS key permissions
- Without KMS, prod account roles would get "Access Denied" trying to decrypt artifacts

## 🔑 The 3 KMS Policy Statements

### **Statement 1: Enable IAM User Permissions**
```hcl
{
  Sid    = "Enable IAM User Permissions"
  Effect = "Allow"
  Principal = {
    AWS = "arn:aws:iam::${var.tooling_account_id}:root"
  }
  Action   = "kms:*"
  Resource = "*"
}
```

**Purpose:** Administrative control
- Gives tooling account **full administrative access** to the KMS key
- Allows tooling account users/roles to manage the key
- **Required by AWS** - without this, you lose control of your own key!

### **Statement 2: Allow AWS Services**
```hcl
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
    "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*",
    "kms:GenerateDataKey*", "kms:DescribeKey"
  ]
  Resource = "*"
}
```

**Purpose:** Service operations
- Allows **CodePipeline** to encrypt artifacts when storing in S3
- Allows **CodeBuild** to decrypt source code and encrypt build outputs
- These services run in the tooling account but need explicit KMS permissions

### **Statement 3: Cross-Account Access**
```hcl
{
  Sid    = "Allow cross-account access from prod account"
  Effect = "Allow"
  Principal = {
    AWS = [
      var.codepipeline_role_arn,    # Prod account role
      var.cloudformation_role_arn   # Prod account role
    ]
  }
  Action = [
    "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*",
    "kms:GenerateDataKey*", "kms:DescribeKey"
  ]
  Resource = "*"
}
```

**Purpose:** The cross-account magic! 🪄
- Allows **specific roles in prod account** to decrypt artifacts
- **CodePipeline role** needs to download encrypted artifacts from S3
- **CloudFormation role** needs to decrypt templates for deployment

## 🎯 Real-World Example

When pipeline runs:

1. **CodeBuild** (tooling) encrypts build output → S3 (using Statement 2)
2. **CodePipeline** (tooling) triggers cross-account deployment (using Statement 2)  
3. **CodePipeline role** (prod) downloads encrypted artifacts (using Statement 3)
4. **CloudFormation role** (prod) decrypts templates (using Statement 3)

**Without the KMS key:** Step 3 would fail with `Access Denied` - prod account can't decrypt tooling account's encrypted data.

This is why KMS is the **bridge** that makes cross-account CI/CD secure and functional! 🌉
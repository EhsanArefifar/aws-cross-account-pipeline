#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None, capture_output=False):
    """Run a shell command and handle errors."""
    print(f"  → Running: {' '.join(cmd)}")
    try:
        if capture_output:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
            return result.stdout
        else:
            subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if capture_output and e.stderr:
            print(f"Error output: {e.stderr}")
        sys.exit(1)

def check_prerequisites():
    """Check that Phase 1 and Phase 2 outputs exist."""
    print("🔍 Checking prerequisites...")
    
    if not Path("terraform.tfvars").exists():
        print("❌ Error: terraform.tfvars not found")
        sys.exit(1)
    
    # Check Phase 1 outputs
    prod_outputs_file = Path("environments/prod/outputs.json")
    if not prod_outputs_file.exists():
        print("❌ Error: environments/prod/outputs.json not found")
        print("   Run Phase 1 first: python scripts/deploy_phase1_roles.py")
        sys.exit(1)
    
    # Check Phase 2 outputs
    tooling_outputs_file = Path("environments/tooling/outputs.json")
    if not tooling_outputs_file.exists():
        print("❌ Error: environments/tooling/outputs.json not found")
        print("   Run Phase 2 first: python scripts/deploy_phase2_pipeline.py")
        sys.exit(1)
    
    # Load and validate outputs
    try:
        with open(prod_outputs_file) as f:
            prod_outputs = json.load(f)
        
        with open(tooling_outputs_file) as f:
            tooling_outputs = json.load(f)
        
        # Validate required outputs
        required_prod = ["codepipeline_role_arn", "cloudformation_role_arn"]
        required_tooling = ["artifact_bucket_name", "artifact_bucket_arn", "kms_key_arn"]
        
        for output in required_prod:
            if output not in prod_outputs:
                print(f"❌ Error: Missing {output} in prod outputs")
                sys.exit(1)
        
        for output in required_tooling:
            if output not in tooling_outputs:
                print(f"❌ Error: Missing {output} in tooling outputs")
                sys.exit(1)
        
        print("✅ Prerequisites check passed")
        return prod_outputs, tooling_outputs
        
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in outputs: {e}")
        sys.exit(1)

def create_phase3_config(tooling_outputs):
    """Create temporary Terraform configuration for Phase 3."""
    print("📝 Creating Phase 3 configuration...")
    
    config_content = f'''terraform {{
  required_version = ">= 1.0"
  
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region  = var.region
  profile = "prod"
}}

variable "tooling_account_id" {{
  type = string
}}

variable "region" {{
  type = string
}}

variable "project_name" {{
  type = string
}}

# Phase 3: Deploy roles WITH policies
module "iam_roles" {{
  source = "../../modules/iam-roles"
  
  tooling_account_id = var.tooling_account_id
  prod_account_id    = var.prod_account_id
  project_name       = var.project_name
  
  # Phase 3: Create policies with S3/KMS resources
  create_policies       = true
  artifact_bucket_name  = "{tooling_outputs['artifact_bucket_name']['value']}"
  artifact_bucket_arn   = "{tooling_outputs['artifact_bucket_arn']['value']}"
  kms_key_arn          = "{tooling_outputs['kms_key_arn']['value']}"
}}

output "codepipeline_role_arn" {{
  value = module.iam_roles.codepipeline_role_arn
}}

output "cloudformation_role_arn" {{
  value = module.iam_roles.cloudformation_role_arn
}}
'''
    
    # Write temporary configuration
    temp_config = Path("environments/prod/main_phase3.tf.tmp")
    with open(temp_config, "w") as f:
        f.write(config_content)
    
    return temp_config

def deploy_phase3():
    """Deploy Phase 3 configuration."""
    print("\n📦 Deploying Phase 3: IAM Roles with Complete Policies...")
    
    env_path = Path("environments/prod")
    
    # Backup original config
    original_config = env_path / "main.tf"
    backup_config = env_path / "main.tf.phase1.backup"
    
    print("  → Backing up Phase 1 configuration...")
    original_config.rename(backup_config)
    
    # Use Phase 3 config
    temp_config = env_path / "main_phase3.tf.tmp"
    phase3_config = env_path / "main.tf"
    temp_config.rename(phase3_config)
    
    try:
        # Initialize (in case provider changed)
        print("  → Initializing Terraform...")
        run_command(["terraform", "init"], cwd=env_path)
        
        # Plan
        print("  → Planning changes...")
        run_command([
            "terraform", "plan",
            "-var-file=../../terraform.tfvars",
            "-out=tfplan"
        ], cwd=env_path)
        
        # Apply
        print("  → Applying changes...")
        run_command(["terraform", "apply", "tfplan"], cwd=env_path)
        
        # Capture outputs
        print("  → Capturing outputs...")
        outputs_json = run_command([
            "terraform", "output", "-json"
        ], cwd=env_path, capture_output=True)
        
        # Save outputs
        outputs_file = env_path / "outputs.json"
        with open(outputs_file, "w") as f:
            f.write(outputs_json)
        
        print("✅ Phase 3 deployment successful!")
        return json.loads(outputs_json)
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        # Restore original config on failure
        if phase3_config.exists():
            phase3_config.unlink()
        if backup_config.exists():
            backup_config.rename(original_config)
        raise

def cleanup_temp_files():
    """Clean up temporary files."""
    print("🧹 Cleaning up temporary files...")
    
    env_path = Path("environments/prod")
    backup_config = env_path / "main.tf.phase1.backup"
    
    if backup_config.exists():
        backup_config.unlink()
        print("  → Removed Phase 1 backup")

def display_results(prod_outputs, tooling_outputs):
    """Display final deployment results."""
    print("\n" + "="*70)
    print("🎉 Phase 3 Complete! Cross-Account CI/CD Pipeline Ready!")
    print("="*70)
    
    print("\n🔐 IAM Roles (Production Account):")
    print(f"  CodePipeline Role: {prod_outputs['codepipeline_role_arn']['value']}")
    print(f"  CloudFormation Role: {prod_outputs['cloudformation_role_arn']['value']}")
    print("  ✅ Now have full S3 and KMS permissions")
    
    print("\n🚀 Pipeline Resources (Tooling Account):")
    print(f"  Repository URL: {tooling_outputs['repository_clone_url']['value']}")
    print(f"  Pipeline Name: {tooling_outputs['pipeline_name']['value']}")
    print(f"  S3 Bucket: {tooling_outputs['artifact_bucket_name']['value']}")
    
    print("\n🎯 What's Solved:")
    print("  ✅ Circular dependency resolved")
    print("  ✅ Cross-account KMS permissions configured")
    print("  ✅ S3 artifact bucket permissions set")
    print("  ✅ IAM roles have complete policies")
    
    print("\n👉 Next Steps:")
    print("  1. Add application code to repository")
    print("  2. Test pipeline deployment")
    print("  3. Validate cross-account functionality")

def main():
    print("🔄 Starting Phase 3: Complete IAM Policies")
    print("=" * 45)
    
    # Check prerequisites
    prod_outputs, tooling_outputs = check_prerequisites()
    
    # Create Phase 3 configuration
    temp_config = create_phase3_config(tooling_outputs)
    
    try:
        # Deploy Phase 3
        updated_prod_outputs = deploy_phase3()
        
        # Clean up
        cleanup_temp_files()
        
        # Display results
        display_results(updated_prod_outputs, tooling_outputs)
        
    except Exception as e:
        print(f"\n❌ Phase 3 failed: {e}")
        # Clean up temp files
        if temp_config.exists():
            temp_config.unlink()
        sys.exit(1)

if __name__ == "__main__":
    main()
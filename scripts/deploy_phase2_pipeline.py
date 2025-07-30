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
    """Check that Phase 1 outputs exist."""
    print("🔍 Checking prerequisites...")
    
    if not Path("terraform.tfvars").exists():
        print("❌ Error: terraform.tfvars not found")
        sys.exit(1)
    
    prod_outputs_file = Path("environments/prod/outputs.json")
    if not prod_outputs_file.exists():
        print("❌ Error: environments/prod/outputs.json not found")
        print("   Run Phase 1 first: python scripts/deploy_phase1_roles.py")
        sys.exit(1)
    
    # Validate outputs contain required role ARNs
    try:
        with open(prod_outputs_file) as f:
            outputs = json.load(f)
        
        required_outputs = ["codepipeline_role_arn", "cloudformation_role_arn"]
        for output in required_outputs:
            if output not in outputs:
                print(f"❌ Error: Missing {output} in prod outputs")
                sys.exit(1)
        
        print("✅ Prerequisites check passed")
        return outputs
        
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in prod outputs: {e}")
        sys.exit(1)

def deploy_environment(env_name):
    """Deploy Terraform configuration for an environment."""
    print(f"\n📦 Deploying to {env_name} environment...")
    
    env_path = Path(f"environments/{env_name}")
    
    # Initialize Terraform
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
    
    # Save outputs to file
    outputs_file = env_path / "outputs.json"
    with open(outputs_file, "w") as f:
        f.write(outputs_json)
    
    print(f"✅ {env_name} environment deployed successfully!")
    return json.loads(outputs_json)

def display_results(tooling_outputs, prod_outputs):
    """Display deployment results."""
    print("\n" + "="*60)
    print("✨ Phase 2 Complete! Pipeline infrastructure created.")
    print("="*60)
    
    print("\n📝 Pipeline Resources Created:")
    print(f"  Repository URL: {tooling_outputs['repository_clone_url']['value']}")
    print(f"  Pipeline Name: {tooling_outputs['pipeline_name']['value']}")
    print(f"  S3 Bucket: {tooling_outputs['artifact_bucket_name']['value']}")
    print(f"  KMS Key ARN: {tooling_outputs['kms_key_arn']['value']}")
    
    print("\n🔗 Cross-Account Configuration:")
    print(f"  CodePipeline Role: {prod_outputs['codepipeline_role_arn']['value']}")
    print(f"  CloudFormation Role: {prod_outputs['cloudformation_role_arn']['value']}")
    
    print("\n👉 Next Steps:")
    print("  1. Add application code to the repository")
    print("  2. Run Phase 3 to complete IAM policies")
    print("  3. Test the pipeline deployment")

def main():
    print("🚀 Starting Phase 2: Pipeline Infrastructure Deployment")
    print("=" * 58)
    
    # Check prerequisites
    prod_outputs = check_prerequisites()
    
    # Deploy to tooling environment
    tooling_outputs = deploy_environment("tooling")
    
    # Display results
    display_results(tooling_outputs, prod_outputs)

if __name__ == "__main__":
    main()
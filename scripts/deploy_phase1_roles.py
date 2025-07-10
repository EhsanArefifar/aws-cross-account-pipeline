import os
import sys
import json
import subprocess
from pathlib import Path



def run_command(cmd, cwd=None, capture_output=False):
    """
    Run a shell command and handle errors.
    """
    print(f" ➡️ Running {' '.join(cmd)}")
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

def deploy_environment(env_name):
    """"
    Deploy Terraform config for an environement
    """
    print(f"\n📦 Deploying to {env_name} environment...")

    env_path = Path(f"environments/{env_name}")

    #Initialize Terraform
    print(f" ➡️ Initializing Terraform...")
    run_command(["terraform", "init"], cwd=env_path)

    # Plan
    print("  ➡️ Planning changes...")
    run_command([
        "terraform", "plan",
        "-var-file=../../terraform.tfvars",
        "-out=tfplan"
    ], cwd=env_path)
    
    # Apply
    print("  ➡️ Applying changes...")
    run_command(["terraform", "apply", "tfplan"], cwd=env_path)

    # Capture outputs
    print("  ➡️ Capturing outputs...")
    outputs_json = run_command([
        "terraform", "output", "-json"
    ], cwd=env_path, capture_output=True)
    
    # Save outputs to file
    outputs_file = env_path / "outputs.json"
    with open(outputs_file, "w") as f:
        f.write(outputs_json)
    
    print(f"✅ {env_name} environment deployed successfully!")
    return json.loads(outputs_json)


def main():
    print(f"🚀 Starting Phase 1> Deploying IAM roles without Policies")
    print("=" * 55)

    #check prerequisites
    if not Path("terraform.tfvars").exists():
        print(f"❌ Error: Terraform.tfvars not found")
        sys.exit(1)
    
    # Deploy to prod environment
    prod_outputs = deploy_environment("prod")

    # Display results
    print("\n✨ Phase 1 Complete! IAM roles created without policies.")
    print("\n📝 Role ARNs created:")
    print(f"  CodePipeline Role: {prod_outputs['codepipeline_role_arn']['value']}")
    print(f"  CloudFormation Role: {prod_outputs['cloudformation_role_arn']['value']}")
    print("\n👉 Next: Deploy the pipeline in the tooling account (Phase 2)")

if __name__ == "__main__":
    main()



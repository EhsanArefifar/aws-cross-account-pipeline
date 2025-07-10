#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

def check_aws_resource(profile, service, check_cmd):
    """Check if an AWS resource exists."""
    try:
        result = subprocess.run(
            ["aws", service] + check_cmd + ["--profile", profile],
            capture_output=True, text=True, check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError:
        return False, None

def check_role(profile, role_name):
    """Check if an IAM role exists and has no policies."""
    print(f"  Checking {role_name}: ", end="")
    
    # Check if role exists
    exists, output = check_aws_resource(profile, "iam", ["get-role", "--role-name", role_name])
    if not exists:
        print("❌ Not found")
        return False
    
    print("✅ Exists")
    
    # Check policies (should be empty in Phase 1)
    exists, policies_output = check_aws_resource(
        profile, "iam", 
        ["list-role-policies", "--role-name", role_name]
    )
    
    if exists:
        policies = json.loads(policies_output)
        policy_count = len(policies.get("PolicyNames", []))
        if policy_count == 0:
            print(f"    ✅ No policies attached (correct for Phase 1)")
        else:
            print(f"    ⚠️  Warning: {policy_count} policies found (should be 0)")
    
    return True

def main():
    print("🔍 Validating Phase 1: IAM Roles Deployment")
    print("=" * 43)
    
    # Check if outputs file exists
    outputs_file = Path("environments/prod/outputs.json")
    if not outputs_file.exists():
        print("❌ Error: outputs.json not found. Run deploy_phase1_roles.py first.")
        sys.exit(1)
    
    # Load outputs
    with open(outputs_file) as f:
        outputs = json.load(f)
    
    print("\n📋 Checking Production Account Roles:")
    
    # Check both roles
    all_good = True
    all_good &= check_role("prod", "CodePipelineCrossAccountRole")
    all_good &= check_role("prod", "CloudFormationDeploymentRole")
    
    # Display captured ARNs
    print("\n📋 Captured Role ARNs:")
    print(f"  CodePipeline: {outputs['codepipeline_role_arn']['value']}")
    print(f"  CloudFormation: {outputs['cloudformation_role_arn']['value']}")
    
    if all_good:
        print("\n✅ Phase 1 validation complete!")
        print("👉 You're ready to proceed to Chapter 3: Creating the Pipeline")
    else:
        print("\n❌ Validation failed. Please check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
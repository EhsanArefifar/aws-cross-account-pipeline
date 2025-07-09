import os
import sys
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def check_aws_profile(profile):
    print(f"AWS Profile '{profile}': ", end="")
    try:
        # Initialize a session using the given profile
        session = boto3.Session(profile_name=profile)
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        print(f"✅ (Account: {account_id})")
    except (BotoCoreError, ClientError) as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

def check_directories(dirs):
    print("\nDirectory Structure:")
    for d in dirs:
        if os.path.isdir(d):
            print(f"✅ {d}")
        else:
            print(f"❌ {d} missing")

def check_tfvars(file_path="terraform.tfvars"):
    print("\nConfiguration:")
    if os.path.isfile(file_path):
        print(f"✅ {file_path} exists")
        with open(file_path) as f:
            content = f.read()
            if "tooling_account_id" in content:
                print("  ✅ tooling_account_id set")
            else:
                print("  ❌ tooling_account_id missing")
            if "prod_account_id" in content:
                print("  ✅ prod_account_id set")
            else:
                print("  ❌ prod_account_id missing")
    else:
        print(f"❌ {file_path} missing")

def main():
    print("🔍 Validating Foundation Setup")
    print("==============================")

    for profile in ["tooling", "prod"]:
        check_aws_profile(profile)

    dirs = [
        "modules/iam-roles", "modules/pipeline", "environments/tooling",
        "environments/prod", "application", "scripts"
    ]
    check_directories(dirs)
    check_tfvars()

    print("\n✅ Foundation setup complete!")

if __name__ == "__main__":
    main()

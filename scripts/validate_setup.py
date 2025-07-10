import os
import sys
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def check_aws_profile(profile):
    print(f"AWS Profile '{profile}':", end="")
    
    try:
        #Initialize a session by the given profile
        session = boto3.Session(profile_name=profile)
        sts = session.client('sts')

        identity = sts.get_caller_identity()
        account_id = identity["Account"]
        print(f"✅ (Account: {account_id})")

    except (BotoCoreError, ClientError) as e:
        print(f"❌ failed: {e}")
        sys.exit(1)

def check_directories(dirs):
    print(f"\nDirectory structure>")

    for dir in dirs:
        if os.path.isdir(dir):
            print(f"✅ {dir}")
        else:
            print(f"❌ {dir} missing")


def check_configuration(file_path="terraform.tfvars"):
    print(f"\nConfiguration:")

    if os.path.isfile(file_path):
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
        print(f" ❌ {file_path} missing")

def main():

    Profiles = ["tooling", "prod"]

    for profile in Profiles:
        check_aws_profile(profile)
    
    dirs = [
        "modules/iam-roles", "modules/pipeline",
        "environments/tooling", "environments/prod",
        "application/app", "application/buildspec", "application/infrastructure",
        "scripts"
    ]

    check_directories(dirs)
    check_configuration()    

    print(f"\n ✅ Foundation setup completed!")
        
if __name__ == "__main__":
    main()
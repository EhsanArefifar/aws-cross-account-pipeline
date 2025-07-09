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
    pass

def check_configuration():
    pass




def main():

    Profiles = ["tooling", "prod"]

    for profile in Profiles:
        check_aws_profile(profile)
        
if __name__ == "__main__":
    main()
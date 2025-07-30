#!/usr/bin/env python3
import json
import boto3
import sys
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

def load_outputs():
    """Load outputs from all phases."""
    try:
        with open("environments/prod/outputs.json") as f:
            prod_outputs = json.load(f)
        
        with open("environments/tooling/outputs.json") as f:
            tooling_outputs = json.load(f)
        
        return prod_outputs, tooling_outputs
    except FileNotFoundError as e:
        print(f"❌ Error: Output file not found: {e}")
        print("   Make sure all phases have been deployed successfully.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in outputs: {e}")
        sys.exit(1)

def test_tooling_account_access(tooling_outputs):
    """Test access to resources in tooling account."""
    print("🔍 Testing Tooling Account Resources...")
    
    try:
        # Create tooling account session
        session = boto3.Session(profile_name='tooling')
        
        # Test S3 bucket access
        s3_client = session.client('s3')
        bucket_name = tooling_outputs['artifact_bucket_name']['value']
        
        print(f"  → Testing S3 bucket: {bucket_name}")
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print("    ✅ S3 bucket accessible")
        except ClientError as e:
            print(f"    ❌ S3 bucket access failed: {e}")
            return False
        
        # Test KMS key access
        kms_client = session.client('kms')
        kms_key_arn = tooling_outputs['kms_key_arn']['value']
        kms_key_id = kms_key_arn.split('/')[-1]
        
        print(f"  → Testing KMS key: {kms_key_id}")
        try:
            kms_client.describe_key(KeyId=kms_key_id)
            print("    ✅ KMS key accessible")
        except ClientError as e:
            print(f"    ❌ KMS key access failed: {e}")
            return False
        
        # Test CodeCommit repository
        codecommit_client = session.client('codecommit')
        repo_name = tooling_outputs['repository_clone_url']['value'].split('/')[-1].replace('.git', '')
        
        print(f"  → Testing CodeCommit repository: {repo_name}")
        try:
            codecommit_client.get_repository(repositoryName=repo_name)
            print("    ✅ CodeCommit repository accessible")
        except ClientError as e:
            print(f"    ❌ CodeCommit repository access failed: {e}")
            return False
        
        # Test CodePipeline
        codepipeline_client = session.client('codepipeline')
        pipeline_name = tooling_outputs['pipeline_name']['value']
        
        print(f"  → Testing CodePipeline: {pipeline_name}")
        try:
            codepipeline_client.get_pipeline(name=pipeline_name)
            print("    ✅ CodePipeline accessible")
        except ClientError as e:
            print(f"    ❌ CodePipeline access failed: {e}")
            return False
        
        return True
        
    except NoCredentialsError:
        print("❌ Error: No credentials found for tooling account")
        print("   Make sure AWS profile 'tooling' is configured")
        return False
    except Exception as e:
        print(f"❌ Error testing tooling account: {e}")
        return False

def test_prod_account_access(prod_outputs):
    """Test access to resources in prod account."""
    print("\n🔍 Testing Production Account Resources...")
    
    try:
        # Create prod account session
        session = boto3.Session(profile_name='prod')
        iam_client = session.client('iam')
        
        # Test CodePipeline role
        codepipeline_role_arn = prod_outputs['codepipeline_role_arn']['value']
        role_name = codepipeline_role_arn.split('/')[-1]
        
        print(f"  → Testing CodePipeline role: {role_name}")
        try:
            role = iam_client.get_role(RoleName=role_name)
            print("    ✅ CodePipeline role exists")
            
            # Check if role has policies
            policies = iam_client.list_role_policies(RoleName=role_name)
            if policies['PolicyNames']:
                print(f"    ✅ Role has {len(policies['PolicyNames'])} inline policies")
            else:
                print("    ⚠️  Role has no inline policies (Phase 3 might not be complete)")
                
        except ClientError as e:
            print(f"    ❌ CodePipeline role access failed: {e}")
            return False
        
        # Test CloudFormation role
        cf_role_arn = prod_outputs['cloudformation_role_arn']['value']
        cf_role_name = cf_role_arn.split('/')[-1]
        
        print(f"  → Testing CloudFormation role: {cf_role_name}")
        try:
            role = iam_client.get_role(RoleName=cf_role_name)
            print("    ✅ CloudFormation role exists")
            
            # Check if role has policies
            policies = iam_client.list_role_policies(RoleName=cf_role_name)
            if policies['PolicyNames']:
                print(f"    ✅ Role has {len(policies['PolicyNames'])} inline policies")
            else:
                print("    ⚠️  Role has no inline policies (Phase 3 might not be complete)")
                
        except ClientError as e:
            print(f"    ❌ CloudFormation role access failed: {e}")
            return False
        
        return True
        
    except NoCredentialsError:
        print("❌ Error: No credentials found for prod account")
        print("   Make sure AWS profile 'prod' is configured")
        return False
    except Exception as e:
        print(f"❌ Error testing prod account: {e}")
        return False

def test_cross_account_permissions(prod_outputs, tooling_outputs):
    """Test cross-account permissions by attempting to assume roles."""
    print("\n🔗 Testing Cross-Account Permissions...")
    
    try:
        # Test from tooling account - can we assume prod roles?
        tooling_session = boto3.Session(profile_name='tooling')
        sts_client = tooling_session.client('sts')
        
        # Test assuming CodePipeline role
        codepipeline_role_arn = prod_outputs['codepipeline_role_arn']['value']
        print(f"  → Testing assume role: {codepipeline_role_arn.split('/')[-1]}")
        
        try:
            assumed_role = sts_client.assume_role(
                RoleArn=codepipeline_role_arn,
                RoleSessionName='ValidationTest'
            )
            print("    ✅ Successfully assumed CodePipeline role")
            
            # Test S3 access with assumed role
            assumed_credentials = assumed_role['Credentials']
            s3_client = boto3.client(
                's3',
                aws_access_key_id=assumed_credentials['AccessKeyId'],
                aws_secret_access_key=assumed_credentials['SecretAccessKey'],
                aws_session_token=assumed_credentials['SessionToken']
            )
            
            bucket_name = tooling_outputs['artifact_bucket_name']['value']
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                print("    ✅ Cross-account S3 access working")
            except ClientError as e:
                print(f"    ❌ Cross-account S3 access failed: {e}")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                print("    ❌ Cannot assume role - check trust relationship")
            else:
                print(f"    ❌ Role assumption failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing cross-account permissions: {e}")
        return False

def display_summary(tooling_ok, prod_ok, cross_account_ok):
    """Display validation summary."""
    print("\n" + "="*60)
    print("📊 Validation Summary")
    print("="*60)
    
    print(f"\n🏢 Tooling Account Resources: {'✅ OK' if tooling_ok else '❌ FAILED'}")
    print(f"🏭 Production Account Resources: {'✅ OK' if prod_ok else '❌ FAILED'}")
    print(f"🔗 Cross-Account Permissions: {'✅ OK' if cross_account_ok else '❌ FAILED'}")
    
    if tooling_ok and prod_ok and cross_account_ok:
        print("\n🎉 All validations passed! Your cross-account CI/CD pipeline is ready!")
        print("\n👉 Next steps:")
        print("  1. Add your application code to the CodeCommit repository")
        print("  2. Create a buildspec.yml file")
        print("  3. Trigger the pipeline by pushing code")
    else:
        print("\n⚠️  Some validations failed. Please check the errors above.")
        print("\n🔧 Common fixes:")
        if not tooling_ok:
            print("  - Check tooling account AWS profile configuration")
            print("  - Verify Phase 2 deployment completed successfully")
        if not prod_ok:
            print("  - Check prod account AWS profile configuration")
            print("  - Verify Phases 1 and 3 deployment completed successfully")
        if not cross_account_ok:
            print("  - Verify all three phases completed successfully")
            print("  - Check IAM role trust relationships")

def main():
    print("🔍 Cross-Account CI/CD Pipeline Validation")
    print("=" * 45)
    
    # Load outputs
    prod_outputs, tooling_outputs = load_outputs()
    
    # Run tests
    tooling_ok = test_tooling_account_access(tooling_outputs)
    prod_ok = test_prod_account_access(prod_outputs)
    cross_account_ok = test_cross_account_permissions(prod_outputs, tooling_outputs) if tooling_ok and prod_ok else False
    
    # Display summary
    display_summary(tooling_ok, prod_ok, cross_account_ok)
    
    # Exit with appropriate code
    if tooling_ok and prod_ok and cross_account_ok:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
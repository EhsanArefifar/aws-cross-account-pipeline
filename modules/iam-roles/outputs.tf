output "codepipeline_role_arn" {
    description = "ARN of the CodePipeline cross-account role."  
    value = aws_iam_role.codepipeline_cross_account.arn
}

output "cloudformation_role_arn" {
    description = "ARN of the CloudFormation deployment role."
    value = aws_iam_role.cloudformation_deployment.arn  
}
# terraform/main.tf

provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias                       = "localstack"
  access_key                  = "test"
  secret_key                  = "test"
  region                      = var.aws_region
  s3_force_path_style         = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    apigateway = "http://localhost:4566"
    dynamodb   = "http://localhost:4566"
    iam        = "http://localhost:4566"
    lambda     = "http://localhost:4566"
    s3         = "http://localhost:4566"
    ssm        = "http://localhost:4566"
  }
}

module "aws_resources" {
  source = "./modules/aws"
  count  = var.use_localstack ? 0 : 1

  providers = {
    aws = aws
  }

  aws_region          = var.aws_region
  lambda_bucket_name  = var.lambda_bucket_name
  dynamodb_table_name = var.dynamodb_table_name
}
#
# module "localstack_resources" {
#   source = "./modules/localstack"
#   count  = var.use_localstack ? 1 : 0
#
#   providers = {
#     aws = aws.localstack
#   }
#
#   aws_region          = var.aws_region
#   lambda_bucket_name  = "${var.lambda_bucket_name}-local"
#   dynamodb_table_name = "${var.dynamodb_table_name}-local"
# }
#

# terraform/variables.tf

variable "aws_region" {
  description = "The AWS region to create resources in"
  default     = "us-west-2"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  default     = "EnvironmentBookings"
  type        = string
}

variable "lambda_bucket_name" {
  description = "The name of the S3 bucket to store Lambda deployment packages"
  default     = "envbooking-lambda-deploy-dev-20230609"
  type        = string
}

variable "use_localstack" {
  description = "Whether to use LocalStack for local development"
  type        = bool
  default     = false
#   default     = true
}
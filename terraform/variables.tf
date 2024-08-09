variable "aws_region" {
  description = "The AWS region to create resources in"
  default     = "us-west-2"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  default     = "EnvironmentBookings"
}

variable "lambda_bucket_name" {
  description = "The name of the S3 bucket to store Lambda deployment packages"
  default     = "envbooking-lambda-deploy-dev-20230609"
}
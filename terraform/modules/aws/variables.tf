variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
}

variable "lambda_bucket_name" {
  description = "The name of the S3 bucket for Lambda packages"
  type        = string
}

variable "dynamodb_table_name" {
  description = "The name of the DynamoDB table"
  type        = string
}

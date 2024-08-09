variable "aws_region" {
  description = "The AWS region to create resources in"
  default     = "us-west-2"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  default     = "EnvironmentBookings"
}
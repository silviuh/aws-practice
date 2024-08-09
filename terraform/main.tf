provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = var.lambda_bucket_name
}

resource "aws_s3_bucket_public_access_block" "lambda_bucket_access" {
  bucket = aws_s3_bucket.lambda_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/../tmp/lambda_package.zip"
  excludes    = ["__pycache__", "*.pyc"]
}

resource "aws_s3_object" "lambda_package" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "lambda_package_${timestamp()}.zip"
  source = data.archive_file.lambda_package.output_path
  etag   = filemd5(data.archive_file.lambda_package.output_path)
}

resource "aws_lambda_function" "slack_command" {
  function_name = "slack-command-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"

  s3_bucket = aws_s3_bucket.lambda_bucket.id
  s3_key    = aws_s3_object.lambda_package.key

  environment {
    variables = {
      DYNAMODB_TABLE  = aws_dynamodb_table.environments_table.name
      SLACK_BOT_TOKEN = "ssm:/slack/bot-token"
    }
  }
}

resource "aws_lambda_function" "initialize_environments" {
  function_name = "initialize-environments-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "initialize_environments_lambda.lambda_handler"
  runtime       = "python3.8"

  s3_bucket = aws_s3_bucket.lambda_bucket.id
  s3_key    = aws_s3_object.lambda_package.key

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.environments_table.name
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "dynamodb_policy" {
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.environments_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/slack/bot-token"
      }
    ]
  })
}

resource "aws_api_gateway_rest_api" "slack_api" {
  name = "slack-command-api"
}

resource "aws_api_gateway_resource" "slack_resource" {
  rest_api_id = aws_api_gateway_rest_api.slack_api.id
  parent_id   = aws_api_gateway_rest_api.slack_api.root_resource_id
  path_part   = "slack-command"
}

resource "aws_api_gateway_method" "slack_method" {
  rest_api_id   = aws_api_gateway_rest_api.slack_api.id
  resource_id   = aws_api_gateway_resource.slack_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "slack_integration" {
  rest_api_id = aws_api_gateway_rest_api.slack_api.id
  resource_id = aws_api_gateway_resource.slack_resource.id
  http_method = aws_api_gateway_method.slack_method.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.slack_command.invoke_arn
}

resource "aws_dynamodb_table" "environments_table" {
  name         = "EnvironmentBookings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "EnvironmentId"

  attribute {
    name = "EnvironmentId"
    type = "S"
  }
}
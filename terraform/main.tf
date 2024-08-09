provider "aws" {
  region = var.aws_region
}

resource "aws_dynamodb_table" "environments_table" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "EnvironmentId"

  attribute {
    name = "EnvironmentId"
    type = "S"
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "environment-booking-lambda-role"

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

resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.environments_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
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

data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/../tmp/lambda_package.zip"
}

resource "aws_lambda_function" "slack_command" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "slack-command-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.8"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE   = aws_dynamodb_table.environments_table.name
      SLACK_BOT_TOKEN  = "ssm:/slack/bot-token"
    }
  }
}

resource "aws_lambda_function" "initialize_environments" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "initialize-environments-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "initialize_environments_lambda.lambda_handler"
  runtime          = "python3.8"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.environments_table.name
    }
  }
}


data "template_file" "api_swagger" {
  template = file("${path.module}/../slack-command-api.yaml")

  vars = {
    lambda_uri = aws_lambda_function.slack_command.invoke_arn
  }
}

resource "aws_api_gateway_rest_api" "api" {
  name = "environment-booking-api"
  body = data.template_file.api_swagger.rendered

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha256(jsonencode(aws_api_gateway_rest_api.api.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api" {
  deployment_id = aws_api_gateway_deployment.api.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = "prod"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.slack_command.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}
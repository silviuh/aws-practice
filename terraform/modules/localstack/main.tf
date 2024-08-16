resource "aws_s3_bucket" "lambda_bucket" {
  provider = aws.localstack
  bucket   = var.lambda_bucket_name
}

resource "aws_s3_bucket_public_access_block" "lambda_bucket_access" {
  provider = aws.localstack
  bucket   = aws_s3_bucket.lambda_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "null_resource" "create_lambda_package" {
  triggers = {
    src_hash     = sha256(join("", [for f in fileset("${path.module}/../../../src", "**"): filesha256("${path.module}/../../../src/${f}")]))
    requirements = filemd5("${path.module}/../../../requirements.txt")
    always_run   = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOT
      mkdir -p ${path.module}/package
      cp -R ${path.module}/../../../src/* ${path.module}/package/
      pip install -r ${path.module}/../../../requirements.txt -t ${path.module}/package/
      cd ${path.module}/package
      echo "Package contents:"
      ls -R
      zip -r ${path.module}/lambda_package.zip .
      aws --endpoint-url=http://localhost:4566 s3 cp ${path.module}/lambda_package.zip s3://${aws_s3_bucket.lambda_bucket.id}/lambda_package_$(date +%s).zip
    EOT
  }
}

data "aws_s3_bucket_objects" "lambda_packages" {
  provider   = aws.localstack
  bucket     = aws_s3_bucket.lambda_bucket.id
  prefix     = "lambda_package_"
  depends_on = [null_resource.create_lambda_package]
}

data "aws_s3_object" "lambda_package" {
  provider   = aws.localstack
  bucket     = aws_s3_bucket.lambda_bucket.id
  key        = element(sort(data.aws_s3_bucket_objects.lambda_packages.keys), length(data.aws_s3_bucket_objects.lambda_packages.keys) - 1)
  depends_on = [null_resource.create_lambda_package]
}

resource "aws_lambda_function" "slack_command" {
  provider         = aws.localstack
  function_name    = "slack-command-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.8"
  s3_bucket        = data.aws_s3_object.lambda_package.bucket
  s3_key           = data.aws_s3_object.lambda_package.key
  source_code_hash = data.aws_s3_object.lambda_package.body

  depends_on = [null_resource.create_lambda_package]

  environment {
    variables = {
      DYNAMODB_TABLE  = aws_dynamodb_table.environments_table.name
      SLACK_BOT_TOKEN = "ssm:/slack/bot-token"
    }
  }
}

resource "aws_lambda_function" "initialize_environments" {
  provider         = aws.localstack
  function_name    = "initialize-environments-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "initialize_environments_lambda.lambda_handler"
  runtime          = "python3.8"
  s3_bucket        = data.aws_s3_object.lambda_package.bucket
  s3_key           = data.aws_s3_object.lambda_package.key
  source_code_hash = data.aws_s3_object.lambda_package.body

  depends_on = [null_resource.create_lambda_package]

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.environments_table.name
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  provider = aws.localstack
  name     = "lambda-role"

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
  provider   = aws.localstack
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "dynamodb_policy" {
  provider = aws.localstack
  role     = aws_iam_role.lambda_role.id

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
  provider = aws.localstack
  name     = "slack-command-api-v2"
}

resource "aws_api_gateway_resource" "slack_resource" {
  provider    = aws.localstack
  rest_api_id = aws_api_gateway_rest_api.slack_api.id
  parent_id   = aws_api_gateway_rest_api.slack_api.root_resource_id
  path_part   = "slack-command"
}

resource "aws_api_gateway_resource" "initialize_resource" {
  provider    = aws.localstack
  rest_api_id = aws_api_gateway_rest_api.slack_api.id
  parent_id   = aws_api_gateway_rest_api.slack_api.root_resource_id
  path_part   = "initialize"
}

resource "aws_api_gateway_method" "slack_method" {
  provider      = aws.localstack
  rest_api_id   = aws_api_gateway_rest_api.slack_api.id
  resource_id   = aws_api_gateway_resource.slack_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "initialize_method" {
  provider      = aws.localstack
  rest_api_id   = aws_api_gateway_rest_api.slack_api.id
  resource_id   = aws_api_gateway_resource.initialize_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "slack_integration" {
  provider                = aws.localstack
  rest_api_id             = aws_api_gateway_rest_api.slack_api.id
  resource_id             = aws_api_gateway_resource.slack_resource.id
  http_method             = aws_api_gateway_method.slack_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.slack_command.invoke_arn
}

resource "aws_api_gateway_integration" "initialize_integration" {
  provider                = aws.localstack
  rest_api_id             = aws_api_gateway_rest_api.slack_api.id
  resource_id             = aws_api_gateway_resource.initialize_resource.id
  http_method             = aws_api_gateway_method.initialize_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.initialize_environments.invoke_arn
}

resource "aws_api_gateway_deployment" "api" {
  provider = aws.localstack
  depends_on = [
    aws_api_gateway_integration.slack_integration,
    aws_api_gateway_integration.initialize_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.slack_api.id

  lifecycle {
    create_before_destroy = true
  }

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.slack_resource.id,
      aws_api_gateway_method.slack_method.id,
      aws_api_gateway_integration.slack_integration.id,

      aws_api_gateway_resource.initialize_resource.id,
      aws_api_gateway_method.initialize_method.id,
      aws_api_gateway_integration.initialize_integration.id,
    ]))
  }
}

resource "aws_api_gateway_stage" "api" {
  provider      = aws.localstack
  deployment_id = aws_api_gateway_deployment.api.id
  rest_api_id   = aws_api_gateway_rest_api.slack_api.id
  stage_name    = "prod"
}

resource "aws_dynamodb_table" "environments_table" {
  provider     = aws.localstack
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "EnvironmentId"

  attribute {
    name = "EnvironmentId"
    type = "S"
  }
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.environments_table.name
}

output "api_gateway_invoke_url" {
  value = "${aws_api_gateway_stage.api.invoke_url}/slack-command"
}

#!/bin/bash

# Set variables
REGION="us-west-2"
SLACK_COMMAND_FUNCTION_NAME="slack-command-lambda"
INIT_ENVIRONMENTS_FUNCTION_NAME="initialize-environments-lambda"

# Update the main Lambda function
aws lambda update-function-code \
    --function-name $SLACK_COMMAND_FUNCTION_NAME \
    --zip-file fileb://../src/lambda_function.zip \
    --region $REGION

echo "Updated $SLACK_COMMAND_FUNCTION_NAME"

# Update the initialize environments Lambda function
aws lambda update-function-code \
    --function-name $INIT_ENVIRONMENTS_FUNCTION_NAME \
    --zip-file fileb://../src/initialize_environments_lambda.zip \
    --region $REGION

echo "Updated $INIT_ENVIRONMENTS_FUNCTION_NAME"

echo "Lambda functions deployed successfully"
#!/bin/bash

# Set the source directory
SRC_DIR="../src"

# Package the main Lambda function
cd $SRC_DIR
zip -r lambda_function.zip lambda_function.py dynamo_operations.py slack_integration.py
echo "Packaged lambda_function.zip"

# Package the initialize environments Lambda function
zip -r initialize_environments_lambda.zip initialize_environments_lambda.py dynamo_operations.py
echo "Packaged initialize_environments_lambda.zip"

# Move back to the scripts directory
cd -

echo "Lambda functions packaged successfully"
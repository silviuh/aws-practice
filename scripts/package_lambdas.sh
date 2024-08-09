#!/bin/bash

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Create a temporary directory for packaging
mkdir -p tmp

# Create a temporary src directory
mkdir -p tmp/src

# Copy the necessary files to the temporary src directory
cp src/*.py tmp/src/

# Package the main Lambda function
cd tmp
zip -r lambda_function.zip src
echo "Packaged lambda_function.zip"

# Package the initialize environments Lambda function
zip -r initialize_environments_lambda.zip src
echo "Packaged initialize_environments_lambda.zip"

cd ..

echo "Lambda functions packaged successfully"
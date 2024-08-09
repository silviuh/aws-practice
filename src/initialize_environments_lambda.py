import os
import sys

# Debugging information
print("Current working directory:", os.getcwd())
print("Contents of current directory:", os.listdir())
print("Python path:", sys.path)
print("Environment variables:", dict(os.environ))

try:
    from dynamo_operations import initialize_environments
    print("Successfully imported initialize_environments from dynamo_operations")
except ImportError as e:
    print(f"Error importing initialize_environments: {e}")

def lambda_handler(event, context):
    try:
        initialize_environments(env_count=5)
        return {
            'statusCode': 200,
            'body': 'Environment initialization complete.'
        }
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error during initialization: {str(e)}'
        }
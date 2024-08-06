from src.dynamo_operations import initialize_environments

def lambda_handler(event, context):
    initialize_environments(env_count=5)
    return {
        'statusCode': 200,
        'body': 'Environment initialization complete.'
    }

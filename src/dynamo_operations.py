import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import time

boto3.setup_default_session(region_name='us-west-2')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('EnvironmentBookings')

def get_environment(env_id):
    try:
        response = table.get_item(Key={'EnvironmentId': env_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting environment {env_id}: {e.response['Error']['Message']}")
        return None

def book_environment(env_id, user, reason):
    try:
        response = table.update_item(
            Key={'EnvironmentId': env_id},
            UpdateExpression="SET #status = :booked, BookedBy = :user, #reason = :reason, TimestampBooked = :timestamp",
            ConditionExpression="#status = :available",
            ExpressionAttributeNames={
                '#status': 'Status',
                '#reason': 'Reason'
            },
            ExpressionAttributeValues={
                ':booked': 'Booked',
                ':available': 'Available',
                ':user': user,
                ':reason': reason,
                ':timestamp': int(time.time())
            },
            ReturnValues="UPDATED_NEW"
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        print(f"Error booking environment {env_id}: {e.response['Error']['Message']}")
        raise

def return_environment(env_id, user):
    try:
        response = table.update_item(
            Key={'EnvironmentId': env_id},
            UpdateExpression="SET #status = :available, BookedBy = :empty, #reason = :empty, TimestampBooked = :timestamp",
            ConditionExpression="BookedBy = :user",
            ExpressionAttributeNames={
                '#status': 'Status',
                '#reason': 'Reason'
            },
            ExpressionAttributeValues={
                ':available': 'Available',
                ':user': user,
                ':empty': '',
                ':timestamp': 0
            },
            ReturnValues="UPDATED_NEW"
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        print(f"Error returning environment {env_id}: {e.response['Error']['Message']}")
        raise

def get_all_environments():
    try:
        response = table.scan()
        return response['Items']
    except ClientError as e:
        print(f"Error getting all environments: {e.response['Error']['Message']}")
        return []

def evict_environment(env_id):
    try:
        response = table.update_item(
            Key={'EnvironmentId': env_id},
            UpdateExpression="SET #status = :available, BookedBy = :empty, #reason = :empty, TimestampBooked = :timestamp",
            ConditionExpression="#status = :booked",
            ExpressionAttributeNames={
                '#status': 'Status',
                '#reason': 'Reason'
            },
            ExpressionAttributeValues={
                ':available': 'Available',
                ':booked': 'Booked',
                ':empty': '',
                ':timestamp': 0
            },
            ReturnValues="UPDATED_NEW"
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        print(f"Error evicting environment {env_id}: {e.response['Error']['Message']}")
        raise

def initialize_environments(env_count=5):
    for i in range(1, env_count + 1):
        env_id = f"dev-{i}"
        try:
            table.put_item(
                Item={
                    'EnvironmentId': env_id,
                    'Status': 'Available',
                    'BookedBy': '',
                    'Reason': '',
                    'TimestampBooked': 0
                },
                ConditionExpression='attribute_not_exists(EnvironmentId)'
            )
            print(f"Initialized environment {env_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"Environment {env_id} already exists, skipping")
            else:
                print(f"Error initializing environment {env_id}: {e.response['Error']['Message']}")
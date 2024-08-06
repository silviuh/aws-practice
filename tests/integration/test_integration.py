import pytest
import boto3
from moto import mock_dynamodb2
import os
from src.lambda_function import lambda_handler
from src.dynamo_operations import initialize_environments

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture(scope='function')
def dynamodb(aws_credentials):
    with mock_dynamodb2():
        yield boto3.resource('dynamodb', region_name='us-west-2')

@pytest.fixture(scope='function')
def dynamodb_table(dynamodb):
    table = dynamodb.create_table(
        TableName='EnvironmentBookings',
        KeySchema=[{'AttributeName': 'EnvironmentId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'EnvironmentId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    initialize_environments(5)  # Initialize with 5 environments
    return table

@pytest.fixture
def mock_send_message():
    with patch('src.slack_integration.send_message') as mock:
        yield mock

def test_integration_book_and_return(dynamodb_table, mock_send_message):
    # Book an environment
    book_event = {
        'body': 'command=/book&text=dev-1 for Testing&user_name=user1&channel_id=C12345'
    }
    result = lambda_handler(book_event, None)
    assert result['statusCode'] == 200
    assert "booked successfully" in result['body']
    mock_send_message.assert_called_once()
    mock_send_message.reset_mock()

    # Verify the booking in DynamoDB
    item = dynamodb_table.get_item(Key={'EnvironmentId': 'dev-1'})['Item']
    assert item['Status'] == 'Booked'
    assert item['BookedBy'] == 'user1'
    assert item['Reason'] == 'Testing'

    # Return the environment
    return_event = {
        'body': 'command=/return&text=dev-1&user_name=user1&channel_id=C12345'
    }
    result = lambda_handler(return_event, None)
    assert result['statusCode'] == 200
    assert "returned successfully" in result['body']
    mock_send_message.assert_called_once()

    # Verify the return in DynamoDB
    item = dynamodb_table.get_item(Key={'EnvironmentId': 'dev-1'})['Item']
    assert item['Status'] == 'Available'
    assert item['BookedBy'] == ''
    assert item['Reason'] == ''

def test_integration_status(dynamodb_table, mock_send_message):
    # Book an environment first
    book_event = {
        'body': 'command=/book&text=dev-1 for Testing&user_name=user1&channel_id=C12345'
    }
    lambda_handler(book_event, None)
    mock_send_message.reset_mock()

    # Check status
    status_event = {
        'body': 'command=/stat&user_name=user1&channel_id=C12345'
    }
    result = lambda_handler(status_event, None)
    assert result['statusCode'] == 200
    assert "Environment Status" in result['body']
    assert "dev-1: Booked by user1 for Testing" in result['body']
    assert "dev-2: Available" in result['body']
    mock_send_message.assert_called_once()

def test_integration_evict(dynamodb_table, mock_send_message):
    # Book an environment first
    book_event = {
        'body': 'command=/book&text=dev-1 for Testing&user_name=user1&channel_id=C12345'
    }
    lambda_handler(book_event, None)
    mock_send_message.reset_mock()

    # Evict the environment
    evict_event = {
        'body': 'command=/evict&text=dev-1&user_name=user2&channel_id=C12345'
    }
    result = lambda_handler(evict_event, None)
    assert result['statusCode'] == 200
    assert "has been evicted" in result['body']
    mock_send_message.assert_called_once()

    # Verify the eviction in DynamoDB
    item = dynamodb_table.get_item(Key={'EnvironmentId': 'dev-1'})['Item']
    assert item['Status'] == 'Available'
    assert item['BookedBy'] == ''
    assert item['Reason'] == ''

def test_integration_invalid_command(dynamodb_table, mock_send_message):
    invalid_event = {
        'body': 'command=/invalid&text=dev-1&user_name=user1&channel_id=C12345'
    }
    result = lambda_handler(invalid_event, None)
    assert result['statusCode'] == 200
    assert "Invalid command" in result['body']
    mock_send_message.assert_called_once()
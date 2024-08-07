import pytest
import boto3
from moto import mock_aws
from botocore.exceptions import ClientError
from src.dynamo_operations import (
    get_environment, book_environment, return_environment,
    get_all_environments, evict_environment, initialize_environments
)


@pytest.fixture(scope='function')
def aws_credentials():
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture(scope='function')
def dynamodb(aws_credentials):
    with mock_aws():
        yield boto3.resource('dynamodb', region_name='us-west-2')


@pytest.fixture(scope='function')
def table(dynamodb):
    table = dynamodb.create_table(
        TableName='EnvironmentBookings',
        KeySchema=[
            {'AttributeName': 'EnvironmentId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'EnvironmentId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    return table


def test_get_environment(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Available'})
    result = get_environment('dev-1')
    assert result == {'EnvironmentId': 'dev-1', 'Status': 'Available'}


def test_book_environment_success(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Available'})
    result = book_environment('dev-1', 'user1', 'Testing')
    assert result is True
    item = table.get_item(Key={'EnvironmentId': 'dev-1'})['Item']
    assert item['Status'] == 'Booked'
    assert item['BookedBy'] == 'user1'
    assert item['Reason'] == 'Testing'


def test_book_environment_already_booked(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Booked', 'BookedBy': 'user2'})
    result = book_environment('dev-1', 'user1', 'Testing')
    assert result is False


def test_return_environment_success(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Booked', 'BookedBy': 'user1'})
    result = return_environment('dev-1', 'user1')
    assert result is True
    item = table.get_item(Key={'EnvironmentId': 'dev-1'})['Item']
    assert item['Status'] == 'Available'
    assert item['BookedBy'] == ''


def test_return_environment_not_booked_by_user(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Booked', 'BookedBy': 'user2'})
    result = return_environment('dev-1', 'user1')
    assert result is False


def test_get_all_environments(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Available'})
    table.put_item(Item={'EnvironmentId': 'dev-2', 'Status': 'Booked', 'BookedBy': 'user1'})
    result = get_all_environments()
    assert len(result) == 2
    assert {'EnvironmentId': 'dev-1', 'Status': 'Available'} in result
    assert {'EnvironmentId': 'dev-2', 'Status': 'Booked', 'BookedBy': 'user1'} in result


def test_evict_environment_success(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Booked', 'BookedBy': 'user1'})
    result = evict_environment('dev-1')
    assert result is True
    item = table.get_item(Key={'EnvironmentId': 'dev-1'})['Item']
    assert item['Status'] == 'Available'
    assert item['BookedBy'] == ''


def test_evict_environment_not_booked(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Available'})
    result = evict_environment('dev-1')
    assert result is False


def test_initialize_environments(table):
    initialize_environments(2)
    items = table.scan()['Items']
    assert len(items) == 2
    assert {'EnvironmentId': 'dev-1', 'Status': 'Available', 'BookedBy': '', 'Reason': '',
            'TimestampBooked': 0} in items
    assert {'EnvironmentId': 'dev-2', 'Status': 'Available', 'BookedBy': '', 'Reason': '',
            'TimestampBooked': 0} in items


def test_initialize_environments_already_exists(table):
    table.put_item(Item={'EnvironmentId': 'dev-1', 'Status': 'Booked', 'BookedBy': 'user1'})
    initialize_environments(2)
    items = table.scan()['Items']
    assert len(items) == 2
    assert {'EnvironmentId': 'dev-1', 'Status': 'Booked', 'BookedBy': 'user1'} in items
    assert {'EnvironmentId': 'dev-2', 'Status': 'Available', 'BookedBy': '', 'Reason': '',
            'TimestampBooked': 0} in items

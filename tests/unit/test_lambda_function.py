import pytest
from unittest.mock import patch, MagicMock
from src.lambda_function import lambda_handler, handle_book, handle_return, handle_status, handle_evict, handle_invalid_command

@pytest.fixture
def mock_dynamo_operations():
    with patch('src.lambda_function.book_environment') as mock_book, \
            patch('src.lambda_function.return_environment') as mock_return, \
            patch('src.lambda_function.get_all_environments') as mock_get_all, \
            patch('src.lambda_function.get_environment') as mock_get:
        yield {
            'book': mock_book,
            'return': mock_return,
            'get_all': mock_get_all,
            'get': mock_get
        }

@pytest.fixture
def mock_send_message():
    with patch('src.lambda_function.send_message') as mock:
        yield mock

def test_lambda_handler_book(mock_dynamo_operations, mock_send_message):
    event = {
        'body': 'command=/book&text=dev-1 for Testing&user_name=user1&channel_id=C12345'
    }
    mock_dynamo_operations['book'].return_value = True
    result = lambda_handler(event, None)
    assert result['statusCode'] == 200
    assert "booked successfully" in result['body']
    mock_send_message.assert_called_once()

def test_lambda_handler_return(mock_dynamo_operations, mock_send_message):
    event = {
        'body': 'command=/return&text=dev-1&user_name=user1&channel_id=C12345'
    }
    mock_dynamo_operations['return'].return_value = True
    result = lambda_handler(event, None)
    assert result['statusCode'] == 200
    assert "returned successfully" in result['body']
    mock_send_message.assert_called_once()

def test_lambda_handler_stat(mock_dynamo_operations, mock_send_message):
    event = {
        'body': 'command=/stat&user_name=user1&channel_id=C12345'
    }
    mock_dynamo_operations['get_all'].return_value = [
        {'EnvironmentId': 'dev-1', 'Status': 'Available'},
        {'EnvironmentId': 'dev-2', 'Status': 'Booked', 'BookedBy': 'user2', 'Reason': 'Testing'}
    ]
    result = lambda_handler(event, None)
    assert result['statusCode'] == 200
    assert "Environment Status" in result['body']
    assert "dev-1: Available" in result['body']
    assert "dev-2: Booked by user2 for Testing" in result['body']
    mock_send_message.assert_called_once()

def test_lambda_handler_evict(mock_dynamo_operations, mock_send_message):
    event = {
        'body': 'command=/evict&text=dev-1&user_name=user1&channel_id=C12345'
    }
    mock_dynamo_operations['get'].return_value = {'EnvironmentId': 'dev-1', 'Status': 'Booked', 'BookedBy': 'user2'}
    mock_dynamo_operations['return'].return_value = True
    result = lambda_handler(event, None)
    assert result['statusCode'] == 200
    assert "has been evicted" in result['body']
    mock_send_message.assert_called_once()

def test_lambda_handler_invalid_command(mock_send_message):
    event = {
        'body': 'command=/invalid&user_name=user1&channel_id=C12345'
    }
    result = lambda_handler(event, None)
    assert result['statusCode'] == 200
    assert "Invalid command" in result['body']
    mock_send_message.assert_called_once()

def test_lambda_handler_missing_fields():
    event = {
        'body': 'user_name=user1'
    }
    result = lambda_handler(event, None)
    assert result['statusCode'] == 400
    assert "Missing required fields" in result['body']

def test_handle_book(mock_dynamo_operations):
    mock_dynamo_operations['book'].return_value = True
    result = handle_book(['dev-1', 'for', 'Testing'], 'user1')
    assert "booked successfully" in result
    mock_dynamo_operations['book'].assert_called_once_with('dev-1', 'user1', 'Testing')

def test_handle_return(mock_dynamo_operations):
    mock_dynamo_operations['return'].return_value = True
    result = handle_return(['dev-1'], 'user1')
    assert "returned successfully" in result
    mock_dynamo_operations['return'].assert_called_once_with('dev-1', 'user1')

def test_handle_status(mock_dynamo_operations):
    mock_dynamo_operations['get_all'].return_value = [
        {'EnvironmentId': 'dev-1', 'Status': 'Available'},
        {'EnvironmentId': 'dev-2', 'Status': 'Booked', 'BookedBy': 'user2', 'Reason': 'Testing'}
    ]
    result = handle_status()
    assert "Environment Status" in result
    assert "dev-1: Available" in result
    assert "dev-2: Booked by user2 for Testing" in result

def test_handle_evict(mock_dynamo_operations):
    mock_dynamo_operations['get'].return_value = {'EnvironmentId': 'dev-1', 'Status': 'Booked', 'BookedBy': 'user2'}
    mock_dynamo_operations['return'].return_value = True
    result = handle_evict(['dev-1'])
    assert "has been evicted" in result
    mock_dynamo_operations['return'].assert_called_once_with('dev-1', 'user2')

def test_handle_invalid_command():
    result = handle_invalid_command()
    assert "Invalid command" in result
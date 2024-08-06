import pytest
from unittest.mock import patch, MagicMock
from slack_sdk.errors import SlackApiError
from src.slack_integration import send_message

@pytest.fixture
def mock_slack_client():
    with patch('src.slack_integration.client') as mock_client:
        yield mock_client

def test_send_message_success(mock_slack_client, caplog):
    mock_response = MagicMock()
    mock_response.data = {'ok': True, 'message': {'ts': '1234567890.123456'}}
    mock_slack_client.chat_postMessage.return_value = mock_response

    channel = 'C12345'
    message = 'Test message'

    result = send_message(channel, message)

    assert result == mock_response
    mock_slack_client.chat_postMessage.assert_called_once_with(
        channel=channel,
        text=message
    )
    assert f"Sending message to channel {channel}: {message}" in caplog.text
    assert f"Message sent: {mock_response}" in caplog.text

def test_send_message_failure(mock_slack_client, caplog):
    error_response = {'error': 'channel_not_found'}
    mock_slack_client.chat_postMessage.side_effect = SlackApiError(
        message='',
        response=MagicMock(data=error_response)
    )

    channel = 'C12345'
    message = 'Test message'

    result = send_message(channel, message)

    assert result is None
    mock_slack_client.chat_postMessage.assert_called_once_with(
        channel=channel,
        text=message
    )
    assert f"Sending message to channel {channel}: {message}" in caplog.text
    assert f"Error sending message: channel_not_found" in caplog.text

@pytest.fixture
def mock_environment_variable():
    with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test-token'}):
        yield

def test_slack_token_from_environment(mock_environment_variable):
    from src.slack_integration import slack_token
    assert slack_token == 'xoxb-test-token'
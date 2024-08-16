from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

def get_slack_client():
    slack_token = os.environ.get("SLACK_BOT_TOKEN", "dummy_token_for_local_testing")
    return WebClient(token=slack_token)

client = get_slack_client()

def send_message(channel, message):
    print(f"SLACK_BOT_TOKEN: {os.environ.get('SLACK_BOT_TOKEN', 'Not set')}")
    try:
        print(f"Sending message to channel {channel}: {message}")
        if os.environ.get('LOCALSTACK_HOSTNAME'):
            print("LocalStack environment detected. Skipping actual Slack message send.")
            return {"ok": True, "message": message}  # Simulate a successful response
        response = client.chat_postMessage(
            channel=channel,
            text=message
        )
        print(f"Message sent: {response}")
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
    return None
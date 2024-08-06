from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

slack_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=slack_token)


def send_message(channel, message):
    # try:
    #     response = client.chat_postMessage(
    #         channel=channel,
    #         text=message
    #     )
    #     return response
    # except SlackApiError as e:
    #     print(f"Error sending message: {e}")
    #     return None
    try:
        print(f"Sending message to channel {channel}: {message}")
        response = client.chat_postMessage(
            channel=channel,
            text=message
        )
        print(f"Message sent: {response}")
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
    return None

import json
import urllib.parse
from src.dynamo_operations import book_environment, return_environment, get_all_environments, get_environment
from src.slack_integration import send_message


def lambda_handler(event, context):
    try:
        body = urllib.parse.parse_qs(event['body'])
        text = body.get('text', [''])[0]
        command = body.get('command', [''])[0].lstrip('/')
        user = body.get('user_name', [''])[0]
        channel = body.get('channel_id', [''])[0]

        print('text is ' + text)
        print('command is ' + command)
        print('user is ' + user)
        print('channel is ' + channel)

        if not all([command, user, channel]):
            raise ValueError("Missing required fields in the request")

        if not command:
            message = handle_invalid_command()
        else:
            command_type = command
            handler = COMMAND_HANDLERS.get(command_type, handle_invalid_command)
            text = text.split()

            print('test is + ' + str(text))

            if command_type in ['book', 'return']:
                message = handler(text, user)
            elif command_type == 'stat':
                message = handler()
            elif command_type == 'evict':
                message = handler(text)
            else:
                message = handler()

        send_message(channel, message)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'response_type': 'in_channel',
                'text': message
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except ValueError as ve:
        error_message = str(ve)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': error_message
            })
        }
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_message
            })
        }


def handle_book(command, user):
    if len(command) < 3:
        return "Invalid book command. Use: book <env_id> for <reason>"
    env_id = command[0]
    reason = ' '.join(command[2:])
    if book_environment(env_id, user, reason):
        return f"Environment {env_id} booked successfully for {reason}."
    return f"Environment {env_id} is already booked."

def handle_return(command, user):
    if len(command) != 1:
        return "Invalid return command. Use: return <env_id>"
    env_id = command[0]
    if return_environment(env_id, user):
        return f"Environment {env_id} returned successfully."
    return f"You can't return {env_id}. It's either not booked or not booked by you."

def handle_status():
    envs = get_all_environments()
    status_messages = ["Environment Status:"]
    for env in envs:
        status = f"Booked by {env['BookedBy']} for {env['Reason']}" if env['Status'] == 'Booked' else 'Available'
        status_messages.append(f"{env['EnvironmentId']}: {status}")
    return ", ".join(status_messages)

def handle_evict(command):
    if len(command) != 1:
        return "Invalid evict command. Use: evict <env_id>"
    env_id = command[0]
    env = get_environment(env_id)
    if env and env['Status'] == 'Booked':
        if return_environment(env_id, env['BookedBy']):
            return f"Environment {env_id} has been evicted."
        return f"Failed to evict {env_id}."
    return f"Environment {env_id} is not booked."

def handle_invalid_command():
    return "Invalid command. Use 'book', 'return', 'status', or 'evict'."

COMMAND_HANDLERS = {
    'book': handle_book,
    'return': handle_return,
    'stat': handle_status,
    'evict': handle_evict
}

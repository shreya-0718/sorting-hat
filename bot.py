import slack
import os
import math
import random
from dotenv import load_dotenv
from pathlib import Path
from flask import Flask, Response, request
from slackeventsapi import SlackEventAdapter
from slack_sdk.errors import SlackApiError

# note to self: ngrok http 5000

# setup stuff:

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']


# functions section
def get_username(user_id):
    try:
        response = client.users_info(user=user_id)
        return response['user']['profile']['display_name']  # or ['real_name'], ['profile']['display_name']
    except SlackApiError as e:
        print(f"Error fetching username: {e.response['error']}")
        return None



# actual code starts here
@app.route('/sortme', methods=['POST'])
def sortme():
    house = random.randint(1,4)
    switcher = {
        1: "Gryffindor ❤️",
        2: "Hufflepuff 💛",
        3: "Ravenclaw 💙",
        4: "Slytherin 💚",
    }
    text = ", you are in... " + switcher.get(house) + "!"

    data = request.form
    user_id = data.get('user_id')
    print(get_username(user_id=user_id))
    channel_id = data.get('channel_id')
    print(f"<@{get_username(user_id)}>" + text)
    # client.chat_postMessage(channel=channel_id, text=f"<@{sortme['user_id']}>" + text)
    return Response(), 200

@slack_event_adapter.on('message')
def message(payLoad):
    event = payLoad.get('event', {})
    if event.get('subtype') == 'bot_message':
        return
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if BOT_ID != user_id:
        client.chat_postMessage(channel=channel_id, text=text) # error before: private channel so groups not channel

if __name__ == "__main__":
    app.run(debug=True)

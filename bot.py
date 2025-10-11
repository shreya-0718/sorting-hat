import slack
import os
import math
import random
import json
from dotenv import load_dotenv
from pathlib import Path
from flask import Flask, Response, request
from slackeventsapi import SlackEventAdapter
from slack_sdk.errors import SlackApiError

from db import init_db, assign_to_house

# note to self: ngrok http 5000

# setup stuff:

init_db()

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
        return response['user']['profile']['display_name'] 
    except SlackApiError as e:
        print(f"Error fetching username: {e.response['error']}")
        return None 


# actual code starts here
@app.route('/sortme', methods=['POST'])
def sortme():
    data = request.form
    user_id = data.get('user_id')
    print(get_username(user_id=user_id))
    channel_id = data.get('channel_id')

    client.chat_postEphemeral( # sends the msg of picking the house
        channel=channel_id,
        user=user_id,
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Choose your Hogwarts house:*"}
            },
            {
                "type": "actions",
                "block_id": "house_buttons",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Gryffindor ❤️"},
                        "value": "gryffindor_choice",
                        "action_id": "choose_house"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Hufflepuff 💛"},
                        "value": "hufflepuff_choice",
                        "action_id": "choose_house"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Ravenclaw 💙"},
                        "value": "ravenclaw_choice",
                        "action_id": "choose_house"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Slytherin 💚"},
                        "value": "slytherin_choice",
                        "action_id": "choose_house"
                    }
                ]
            }
        ],
        text="Choose your house!",
    )
    # client.chat_postMessage(channel=channel_id, text=f"<@{get_username(user_id)}>" + text)
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

@app.route('/slack/interactions', methods=['POST'])
def handle_interactions():
    payload = json.loads(request.form["payload"])
    interaction_type = payload.get("type")

    if interaction_type == "block_actions":
        return handle_block_actions(payload)

    # will add more types later
    else:
        print(f"Unknown interaction type: {interaction_type}")
        return "", 200
    
def handle_block_actions(payload):
    action = payload["actions"][0]
    action_id = action["action_id"]
    block_id = action.get("block_id")
    channel_id = payload["channel"]["id"]
    user_id = payload["user"]["id"]
    value = action.get("value")  # "gryffindor_choice"

    if action_id == "choose_house" and block_id == "house_buttons":
        return handle_house_choice(channel_id, user_id, value)

    return "", 200

def handle_house_choice(channel_id, user_id, value):
    house = value.replace("_choice", "")  
    
    assign_to_house(user_id, house)

    client.chat_postEphemeral(
        channel= channel_id,
        user_id = user_id,
        text=f"You’ve been sorted into *{house.title()}*! Welcome to your house!"
    )
    return "", 200


if __name__ == "__main__": 
    app.run(debug=True)



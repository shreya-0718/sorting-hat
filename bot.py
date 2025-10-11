import slack
import os
import math
import random
import json
from dotenv import load_dotenv
from pathlib import Path
from flask import Flask, Response, request
from slack_sdk.errors import SlackApiError
import threading

from core import env_path, client, slack_event_adapter, app, BOT_ID
from db import init_db, assign_to_house, print_all_assignments
from hogwarts import send_house_buttons, add_user_to_house

# note to self: ngrok http 5000

# setup stuff:

init_db()

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
    channel_id = data.get('channel_id')

    # Respond immediately to avoid timeout
    threading.Thread(target=send_house_buttons, args=(channel_id, user_id)).start()
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
    value = action["value"]  
    channel_id = payload["channel"]["id"]
    user_id = payload["user"]["id"]

    house = value.replace("_choice", "")  
    
    assign_to_house(user_id, house)

    client.chat_postEphemeral(
        channel= channel_id,
        user = user_id,
        text=f"You’ve been sorted into *{house.title()}*! Welcome to your house!"
    )

    add_user_to_house(user_id, house)
    print_all_assignments()


    return "", 200

if __name__ == "__main__": 
    app.run(debug=True)


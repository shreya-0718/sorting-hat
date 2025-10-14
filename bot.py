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
from db import init_db, assign_to_house, print_all_assignments, get_user_house, add_points
from hogwarts import send_house_buttons, add_user_to_house, own_points, house_points, send_leaderboard, magic_quiz
from hogwarts import send_results, score_quiz, add_to_secret, remove_from_secret, react_with_house, react_with_heart
import requests, time

# note to self: ngrok http 5000

# setup stuff:

init_db()

# functions section
def get_username(user_id):
    try:
        response = client.users_info(user=user_id)
        return response['user']['profile']['display_name'] 
    except SlackApiError as e:
        print(f"error fetching username: {e.response['error']}")
        return None 
    
def delete_buttons(response_url, house):
    requests.post(response_url, json={
        "replace_original": True,
        "text": f"You’ve been sorted into *{house.title()}*! Welcome to your house!"
    })

# actual code starts here
@app.route('/sortme', methods=['POST'])
def sortme():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')

    existing_house = get_user_house(user_id)
    if existing_house and not existing_house.startswith("("):
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"You’ve already been sorted into *{existing_house.title()}*!"
        )
        return "", 200

    threading.Thread(target=send_house_buttons, args=(channel_id, user_id)).start()
    return Response(), 200

@app.route('/my-points', methods=['POST'])
def my_points():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')

    threading.Thread(target=own_points, args=(channel_id, user_id)).start()
    return Response(), 200

@app.route('/house-points', methods=['POST'])
def check_house_points():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')

    threading.Thread(target=house_points, args=(channel_id, user_id)).start()
    return Response(), 200

@app.route('/hogwarts-leaderboard', methods=['POST'])
def hogwartsleaderboard():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')

    threading.Thread(target=send_leaderboard, args=(channel_id,)).start()
    return Response(), 200

@app.route('/house-points', methods=['POST'])
def housepoints():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')

    threading.Thread(target=house_points, args=(channel_id, user_id)).start()
    return Response(), 200


@slack_event_adapter.on('message')
def message(payLoad):
    event = payLoad.get('event', {})
    if event.get('subtype') == 'bot_message':
        return
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    ts = event.get('ts')

    if text and (BOT_ID != user_id) and ("house" in text.lower()):
        react_with_house(channel_id, user_id, ts)

    if text and (BOT_ID != user_id):
        if ("gryffindor" in text.lower()):
            react_with_heart(channel_id, ts, "red")
        if ("hufflepuff" in text.lower()):
            react_with_heart(channel_id, ts, "yellow")
        if ("ravenclaw" in text.lower()):
            react_with_heart(channel_id, ts, "blue")
        if ("slytherin" in text.lower()):
            react_with_heart(channel_id, ts, "green")

    return Response(), 200

@app.route('/quiz', methods=['POST'])
def quiz():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    trigger_id = data.get("trigger_id")

    threading.Thread(target=magic_quiz, args=(channel_id, user_id, trigger_id)).start()
    return Response(), 200

@app.route('/alohomora', methods=['POST'])
def alohomora():

    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    secret_channel = os.environ.get("SECRET_CHANNEL_ID")

    threading.Thread(target=add_to_secret, args=(user_id, channel_id, secret_channel)).start()

    return Response(), 200

@app.route('/colloportus', methods=['POST'])
def colloportus():

    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    secret_channel = os.environ.get("SECRET_CHANNEL_ID")

    threading.Thread(target=remove_from_secret, args=(user_id, channel_id, secret_channel)).start()

    return Response(), 200

@app.route('/obscuro', methods=['POST'])
def obscuro():
    data = request.form
    channel_id = data.get('channel_id')
    print("channellll:"+ channel_id)
    user_id = data.get('user_id')
    spoiler = data.get('text')

    response = client.chat_postMessage(channel=channel_id, text=f"Spoiler sent by <@{user_id}> has been hidden... \nClick thread to open, but beware!")
    ts = response["ts"] 

    client.reactions_add(name="speak_no_evil", channel=channel_id, timestamp=ts)

    client.chat_postMessage(channel=channel_id, thread_ts=ts, text=f"Reveal: {spoiler}")

    return Response(), 200

@app.route('/slack/interactions', methods=['POST'])
def handle_interactions():
    payload = json.loads(request.form["payload"])
    interaction_type = payload.get("type")

    if payload["type"] == "view_submission":
        user_id = payload["user"]["id"]
        submitted_answers = extract_answers(payload)

        print("quiz submitted we know we know")

        total_points, feedback = score_quiz(user_id, submitted_answers)
        send_results(user_id, feedback, total_points)
        add_points(user_id, total_points)
        
        return "", 200
    
    if interaction_type == "block_actions":
        action = payload["actions"][0]
        
        if action.get("type") == "radio_buttons":
            print("answer clicked")
            return "", 200

        else:
            return choose_house_block(payload)

    else:
        print(f"Unknown interaction type: {interaction_type}")
        return "", 200
    
def choose_house_block(payload):
    action = payload["actions"][0]
    value = action["value"]  
    channel_id = payload["channel"]["id"]
    user_id = payload["user"]["id"]
    response_url = payload.get("response_url")

    house = value.replace("_choice", "") 
    
    assign_to_house(user_id, house)

    add_user_to_house(user_id, house)
    print_all_assignments()
    delete_buttons(response_url, house)

    return "", 200

def extract_answers(payload):
    answers = {}
    state_values = payload["view"]["state"]["values"]

    # dict = dictionary. action_dict contains my selected answer
    for block_id, action_dict in state_values.items():
        for action_id, answer_data in action_dict.items():
            answers[block_id] = answer_data["selected_option"]["value"]
    
    print(answers)
    return answers
    
    #basically just takes all the answers the user submitted

if __name__ == "__main__": 
    app.run(debug=True)

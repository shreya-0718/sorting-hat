import os
from slack_sdk.errors import SlackApiError
from core import client, env_path

from dotenv import load_dotenv
from pathlib import Path

from db import get_user_points, get_user_house, get_house_points
from datetime import datetime, timedelta
import threading, time

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

HOUSE_GROUP_IDS = {
    "gryffindor": os.environ.get("GRYFFINDOR_GROUP_ID"),
    "hufflepuff": os.environ.get("HUFFLEPUFF_GROUP_ID"),
    "ravenclaw": os.environ.get("RAVENCLAW_GROUP_ID"),
    "slytherin": os.environ.get("SLYTHERIN_GROUP_ID")
}

choose_house = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Choose your Hogwarts house:*"
        }
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Gryffindor ❤️",
                    "emoji": True
                },
                "value": "gryffindor_choice",
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Hufflepuff 💛",
                    "emoji": True
                },
                "value": "hufflepuff_choice",
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Ravenclaw 💙",
                    "emoji": True
                },
                "value": "ravenclaw_choice",
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Slytherin 💚",
                    "emoji": True
                },
                "value": "slytherin_choice",
            }
        ]
    }
]

leaderboard = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*HOUSE POINTS LEADERBOARD!*"
        }
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Gryffindor: {get_house_points('gryffindor')} \nHufflepuff: {get_house_points('hufflepuff')} \nRavenclaw: {get_house_points('ravenclaw')} \nSlytherin: {get_house_points('slytherin')}"
        }
    }
]

def add_user_to_house(user_id, house):
    group_id = HOUSE_GROUP_IDS.get(house)
    if not group_id:
        print(f"no group id for: {house}")
        return

    try:
        # add user to their house
        response = client.usergroups_users_list(usergroup=group_id)
        current_users = response["users"]
        if user_id not in current_users:
            updated_users = current_users + [user_id]
            client.usergroups_users_update(
                usergroup=group_id,
                users=",".join(updated_users)
            )
            print(f"added {user_id} to {house}.")

    except SlackApiError as e:
        print(f"error {e.response['error']}")

def send_house_buttons(channel_id, user_id):
    print(f"channel and id: {channel_id}, user: {user_id}") 

    client.chat_postEphemeral(
        channel=channel_id, 
        user=user_id,
        blocks=choose_house,
        text="Choose your house!"
    )

def own_points(channel_id, user_id):
    print(f"sending own points to user: {user_id}")

    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text=f"You have earned {get_user_points(user_id)} points!"
    )

def house_points(channel_id, user_id):
    print(f"sending house points to user: {user_id}")

    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text=f"Your house, {get_user_house(user_id).title()}, has {get_house_points(get_user_house(user_id))} house points!"
    )

def send_leaderboard(channel_id):
    print(f"sending leaderboard to {channel_id}")

    response = client.chat_postMessage(channel=channel_id, blocks=leaderboard)
    ts = response["ts"] # timestamp :P
    time.sleep(30)
    client.chat_delete(channel=channel_id, ts=ts) # delete leaderboard msg after 30 secs :O
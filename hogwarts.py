import os
from slack_sdk.errors import SlackApiError
from core import client, env_path

from dotenv import load_dotenv
from pathlib import Path

from db import get_user_points, get_user_house, get_house_points, get_quiz, get_quiz_row
from datetime import datetime, timedelta
import threading, time

import html, random

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

    response = client.chat_postMessage(channel=channel_id, blocks=leaderboard)
    ts = response["ts"] # timestamp :P
    time.sleep(30)
    client.chat_delete(channel=channel_id, ts=ts) # delete leaderboard msg after 30 secs :O

def magic_quiz(channel_id, user_id, trigger_id):
    print(f"sending quiz to {user_id}")

    quiz_blocks = build_quiz(get_quiz(user_id))

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "quiz_modal",
            "title": {"type": "plain_text", "text": "Quiz Scroll"},
            "submit": {"type": "plain_text", "text": "Submit Answers"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": quiz_blocks
        }
    )

    # response = client.chat_postEphemeral(channel=channel_id, user=user_id, blocks = quiz_blocks)

def build_quiz(questions):
    blocks = []
    for i, q in enumerate(questions): # unescape converts text back to norm text
        question_txt = html.unescape(q["question"])
        correct = html.unescape(q["correct_answer"])
        incorrect = [
            html.unescape(answer) for answer in (q["incorrect_answers"])
    
        ]

        all_ans = incorrect + [correct]
        random.shuffle(all_ans)

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Question {i+1}:* {question_txt}"
            }
        })
        blocks.append({
            "type": "actions",
            "block_id": f"q{i+1}",
            "elements": [
                {
                    "type": "radio_buttons",
                    "action_id": f"answer_q{i+1}",
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": ans},
                            "value": ans
                        } for ans in all_ans
                    ]
                }
            ]
        })
    return blocks #omg the error was that this was inside the for and not after BRO

def send_results(user_id, feedback, total_points):
    result_txt = f"Congratulations! You earned *{total_points} points*! Here are your results...\n\n"

    for i, (qid, correct, expected, actual) in enumerate(feedback):
        if correct:
            result_txt += f"Question {i + 1}: Correct! \n"
        else:
            result_txt += f"Question {i + 1}: Incorrect... here's the right answer: {expected} \n"

    client.chat_postMessage(
        channel=user_id,
        text=result_txt
    )


def score_quiz(user_id, submitted_answers):
    rows = get_quiz_row(user_id)

    total_points = 0
    feedback = []
    i = 1

    for question_id, correct, difficulty in (rows):
        user_answer = submitted_answers.get(f"q{i}")
        print(user_answer)
        is_correct = (user_answer == correct)
        points = 0
        if is_correct:
            if difficulty == "easy":
                points = 2
            elif difficulty == "medium":
                points = 5
            elif difficulty == "hard":
                points = 10
            total_points += points
            points = 0
        i+=1
        
        feedback.append((question_id, is_correct, correct, user_answer))


    return total_points, feedback

def add_to_secret(user_id, channel_id, secret_channel):
    if user_id in client.conversations_members(channel=secret_channel)["members"]:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"You are already in <#{secret_channel}>!"
        )

    else:
        client.conversations_invite(
            channel=secret_channel,
            users=user_id     
        )

        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"Congratulations! You have now joined <#{secret_channel}>.\nYou can leave at any time :)"
        )

        client.chat_postMessage(
            channel = secret_channel,
            text = f"Welcome to the Common Room, <@{user_id}>!"
        )

        client.chat_postEphemeral(
            channel=secret_channel,
            user=user_id,
            text="Here, you can talk about whatever you like with other fellow witches and wizards!"
        )

def remove_from_secret(user_id, channel_id, secret_channel):
    if user_id in client.conversations_members(channel=secret_channel)["members"]:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"The door creaks shut and locks behind you as you step out of the common room. \nFarewell! We'll miss your magic! "
        )

        client.conversations_kick(
            channel=secret_channel,
            user=user_id
        )
    
    else:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"Vanish??? From where???"
        )
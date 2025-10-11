import os
from slack_sdk.errors import SlackApiError
from core import client, env_path

from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

HOUSE_GROUP_IDS = {
    "gryffindor": os.environ.get("GRYFFINDOR_GROUP_ID"),
    "hufflepuff": os.environ.get("HUFFLEPUFF_GROUP_ID"),
    "ravenclaw": os.environ.get("RAVENCLAW_GROUP_ID"),
    "slytherin": os.environ.get("SLYTHERIN_GROUP_ID")
}

blocks = [
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
        # remove from other houses
        for other_house, other_group_id in HOUSE_GROUP_IDS.items():
            if other_house != house:
                response = client.usergroups_users_list(usergroup=other_group_id)
                current_users = response["users"] # users in that group
                if user_id in current_users:
                    updated_users = [u for u in current_users if u != user_id] # every user except the user we wanna remove
                    client.usergroups_users_update(
                        usergroup=other_group_id,
                        users=",".join(updated_users)
                    )
                    print(f"Removed {user_id} from {other_house}")

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
        blocks=blocks,
        text="Choose your house!"
    )
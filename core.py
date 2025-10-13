import os
from dotenv import load_dotenv
from pathlib import Path
from flask import Flask
from slackeventsapi import SlackEventAdapter
import slack


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
print(f"SLACK_TOKEN: {os.environ.get('SLACK_TOKEN')!r}")

BOT_ID = client.api_call("auth.test")['user_id']
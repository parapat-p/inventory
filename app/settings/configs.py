import os
from dotenv import load_dotenv

load_dotenv("./.env")

PORT = os.environ["PORT"]

PLAYER_IN_ROOM = ["A", "B"]
UTF_8 = "UTF-8"
PASSCODE_MESSAGE = "Invalid passcode"

from os import getenv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
NSFW_THRESHOLD = int(getenv("NSFW_THRESHOLD", .35))

WORKING_DIRECTORY = Path(__file__).parent

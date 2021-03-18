# Used for identify features etc., DO NOT MODIFY
VERSION = "0.2b"
# DO NOT MODIFY END

TIME_BETWEEN_CHECK = 10
TIME_BETWEEN_CLEAR = 3600 # An hour
EXPIRY_TIME = 3600 * 6
HTTP_RETRY = 3
BASE_JSON_DIR = "jsons"
CHANNELS_JSON = "channels.json"
FETCHED_JSON = "fetched.json"

# Send to discord on video privated
ENABLE_PRIVATE_CHECK = False

ENABLED_MODULES = {
    "discord": False,
    "telegram": False
}

DISCORD_WEBHOOK_URL = None

TELEGRAM_BOT_TOKEN = None
TELEGRAM_CHAT_ID = None
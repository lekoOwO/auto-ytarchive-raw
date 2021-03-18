import json
import time
import os

import utils
import getm3u8
import getjson

import const

from addons import discord
from addons import telegram

os.chdir(os.path.dirname(os.path.realpath(__file__)))

if not os.path.exists(const.BASE_JSON_DIR):
    os.makedirs(const.BASE_JSON_DIR)

with open(const.CHANNELS_JSON, encoding="utf8") as f:
    CHANNELS = json.load(f)

# fetched
# {
#   channel_name: {
#       video_id: {
#           m3u8_id: {
#               file,
#               create_time
#           }
#       }
#   }
# }

global save_lock
save_lock = False
def save():
    global save_lock
    while save_lock:
        time.sleep(0.1)

    save_lock = True

    with open(const.FETCHED_JSON, "w", encoding="utf8") as f:
        json.dump(fetched, f, indent=4, ensure_ascii=False)
    
    save_lock = False

if os.path.isfile(const.FETCHED_JSON):
    with open(const.FETCHED_JSON, encoding="utf8") as f:
        fetched = json.load(f)
else:
    fetched = {}
    save()

def clear_expiry():
    utils.log(f" Running clear task.")

    clear_queue = []
    for channel_name in fetched:
        for video_id in fetched[channel_name]:
            for m3u8_id in fetched[channel_name][video_id]["fregments"]:
                if time.time() - fetched[channel_name][video_id]["fregments"][m3u8_id]["create_time"] > const.EXPIRY_TIME:
                    utils.log(f"[{channel_name}] {m3u8_id} has expired. Clearing...")

                    clear_queue.append({
                        "channel_name": channel_name,
                        "video_id": video_id,
                        "m3u8_id": m3u8_id
                    })
    for x in clear_queue:
        try:
            os.remove(fetched[x["channel_name"]][x["video_id"]]["fregments"][x["m3u8_id"]]["file"])
        except:
            utils.warn(f"[{x['channel_name']}] Error occurs when deleting {x['m3u8_id']}. Ignoring...")
        fetched[x["channel_name"]][x["video_id"]]["fregments"].pop(x["m3u8_id"])

    clear_queue = []
    for channel_name in fetched:
        for video_id in fetched[channel_name]:
             if not fetched[channel_name][video_id]["fregments"]:
                 clear_queue.append({
                     "channel_name": channel_name,
                     "video_id": video_id
                 })
    for x in clear_queue:
        utils.log(f"[{x['channel_name']}] {x['video_id']} has all gone. Clearing...")
        fetched[x['channel_name']].pop(x['video_id'])

    save()

try:
    expiry_task = utils.RepeatedTimer(const.TIME_BETWEEN_CLEAR, clear_expiry)

    while True:
        for channel_name, channel_id in CHANNELS.items():

            # Check for privated videos
            if const.ENABLE_PRIVATE_CHECK:
                if channel_name in fetched:
                    for video_id in fetched[channel_name]:
                        # Might not needed, but I do dumb things.
                        if "skipPrivateCheck" not in fetched[channel_name][video_id]:
                            fetched[channel_name][video_id]["skipPrivateCheck"] = False
                            save()
                        elif fetched[channel_name][video_id]["skipPrivateCheck"]:
                            continue

                        status = utils.get_video_status(video_id)

                        if status is utils.PlayabilityStatus.OK:
                            continue

                        if status is utils.PlayabilityStatus.PRIVATED:
                            message = f"[{video_id}](https://youtu.be/{video_id}) is privated on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
                        elif status is utils.PlayabilityStatus.REMOVED:
                            message = f"[{video_id}](https://youtu.be/{video_id}) is removed on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
                        elif status is utils.PlayabilityStatus.COPYRIGHTED:
                            message = f"[{video_id}](https://youtu.be/{video_id}) is copyrighted on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
                        elif status is utils.PlayabilityStatus.UNKNOWN:
                            message = f"[{video_id}](https://youtu.be/{video_id}) occurred sth weird on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
                        elif status is utils.PlayabilityStatus.MEMBERS_ONLY:
                            message = f"[{video_id}](https://youtu.be/{video_id}) is member-only on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
                            
                        if const.ENABLED_MODULES["discord"]:
                            discord.send(const.DISCORD_WEBHOOK_URL, message, const.VERSION)
                        if const.ENABLED_MODULES["telegram"]:
                            telegram.send(const.TELEGRAM_BOT_TOKEN, const.TELEGRAM_CHAT_ID, message)

                        fetched[channel_name][video_id]["skipPrivateCheck"] = True
                        save()
                            
                        utils.log(f"[INFO] {message}")

            is_live = utils.is_live(channel_id)
            if is_live:
                utils.log(f"[{channel_name}] On live!")

                video_url = is_live

                video_id = getjson.get_youtube_id(video_url)
                m3u8_url = getm3u8.get_m3u8(video_url)
                m3u8_id = getm3u8.get_m3u8_id(m3u8_url)

                if channel_name not in fetched:
                    fetched[channel_name] = {
                        video_id: {
                            "fregments": {},
                            "skipPrivateCheck": False
                        }
                    }
                
                if video_id not in fetched[channel_name]:
                    fetched[channel_name][video_id] = {
                        "fregments": {},
                        "skipPrivateCheck": False
                    }

                filepath = os.path.join(const.BASE_JSON_DIR, f"{m3u8_id}.json")
                getjson.get_json(video_url, filepath)

                utils.log(f"[{channel_name}] Saving {m3u8_id}...")

                fetched[channel_name][video_id]["fregments"][m3u8_id] = {
                    "file": filepath,
                    "create_time": time.time()
                }

                save()
            else:
                utils.log(f"[{channel_name}] Not on live.")

            utils.log(f" Sleeping for {const.TIME_BETWEEN_CHECK} secs...")
            time.sleep(const.TIME_BETWEEN_CHECK)
except KeyboardInterrupt:
    utils.log(" Forced stop.")
finally:
    expiry_task.stop()
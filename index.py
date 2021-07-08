import json
import time
import os
import threading

import utils
import getm3u8
import getjson

import const
import text

from addons import telegram
from addons import discord
from addons import pushalert
from addons import fcm

if const.CALLBACK_AFTER_EXPIRY:
    from callback import callback as expiry_callback

if const.CHAT_CALLBACK_AFTER_EXPIRY:
    from callback import chat as chat_callback

os.chdir(os.path.dirname(os.path.realpath(__file__)))

if const.CHAT_DIR:
    import getchat
    global chats
    chats = {}

    if not os.path.exists(const.CHAT_DIR):
        os.makedirs(const.CHAT_DIR)

if not os.path.exists(const.BASE_JSON_DIR):
    os.makedirs(const.BASE_JSON_DIR)

if not os.path.exists(const.LOGS_DIR):
    os.makedirs(const.LOGS_DIR)

with open(const.CHANNELS_JSON, encoding="utf8") as f:
    CHANNELS = json.load(f)

# fetched
# {
#   channel_name: {
#       video_id: {
#           "fregments": {
#                m3u8_id: {
#                   file,
#                   create_time
#                }
#            }
#           "skipPrivateCheck": false          
#       }
#   }
# }

global save_lock
save_lock = threading.Lock()
def save():
    global save_lock
    save_lock.acquire()

    with open(const.FETCHED_JSON, "w", encoding="utf8") as f:
        json.dump(fetched, f, indent=4, ensure_ascii=False)
    
    save_lock.release()

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
        if const.CALLBACK_AFTER_EXPIRY:
            expiry_callback.callback(fetched[x['channel_name']][x['video_id']], channel_name=x['channel_name'], video_id=x['video_id'])
        if "chat" in fetched[x['channel_name']][x['video_id']]:
            try:
                os.remove(fetched[x['channel_name']][x['video_id']]["chat"])
            except:
                utils.warn(f"[{x['channel_name']}] Error occurs when deleting chat file for {x['video_id']}. Ignoring...")
        fetched[x['channel_name']].pop(x['video_id'])

    save()

try:
    clear_expiry()
    expiry_task = utils.RepeatedTimer(const.TIME_BETWEEN_CLEAR, clear_expiry)
    if const.CHAT_DIR:
        def get_channel_name_by_video_id(video_id):
            for channel_name in fetched:
                if video_id in fetched[channel_name]:
                    return channel_name
            return None

        def clear_chat():
            utils.log(f" Running chat instance clearing task.")
            global chats
            to_del = []
            for video_id in chats:
                if chats[video_id].is_finished():
                    if const.CHAT_CALLBACK_AFTER_EXPIRY:
                        channel_name = get_channel_name_by_video_id(video_id)
                        chat_callback.callback(chats[video_id], channel_name=channel_name, video_id=video_id)
                    to_del.append(video_id)
                    utils.log(f" Chat instance {video_id} has been queued to be cleared.")
            for video_id in to_del:
                chats.pop(video_id)
                utils.log(f" Chat instance {video_id} has been cleared.")
            
        chat_expiry_task = utils.RepeatedTimer(const.CHAT_TASK_CLEAR_INTERVAL, clear_chat)

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
                        if status is utils.PlayabilityStatus.ON_LIVE:
                            continue

                        if status is utils.PlayabilityStatus.OFFLINE:
                            continue

                        files = [fetched[channel_name][video_id]["fregments"][m3u8_id]["file"] for m3u8_id in fetched[channel_name][video_id]["fregments"]]
                        log_file_path = os.path.join(const.LOGS_DIR, f"{video_id}.html")
                        if os.path.isfile(log_file_path):
                            files.append(log_file_path)
                        if "chat" in fetched[channel_name][video_id]:
                            if os.path.isfile(fetched[channel_name][video_id]["chat"]):
                                files.append(fetched[channel_name][video_id]["chat"])
                            else:
                                utils.warn(f" Chat file for {video_id} not found. This shouldn't happen, maybe someone stealed it...?")

                        message = text.get_private_check_text(status, video_id).format(video_id=video_id, channel_name=channel_name, channel_id=channel_id)
                        
                        utils.notify(message, files)
                        fetched[channel_name][video_id]["skipPrivateCheck"] = True
                        save()
                            
                        utils.log(f" {message}")

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
                            "skipPrivateCheck": False,
                            "skipOnliveNotify": False,
                            "multiManifestNotify": 1
                        }
                    }
                
                if video_id not in fetched[channel_name]:
                    fetched[channel_name][video_id] = {
                        "fregments": {},
                        "skipPrivateCheck": False,
                        "skipOnliveNotify": False,
                        "multiManifestNotify": 1
                    }

                filepath = os.path.join(const.BASE_JSON_DIR, f"{m3u8_id}.json")
                video_data = getjson.get_json(video_url, filepath)

                if const.CHAT_DIR:
                    if video_id not in chats:
                        utils.log(f"[{channel_name}] Downloading chat...")
                        start_timestamp = video_data["metadata"]["startTimestamp"] if "startTimestamp" in video_data["metadata"] else None
                        chat_file = os.path.join(const.CHAT_DIR, f"{video_id}.chat")
                        chats[video_id] = getchat.ChatArchiver(video_url, chat_file, start_timestamp=start_timestamp)
                        fetched[channel_name][video_id]["chat"] = chat_file

                if not fetched[channel_name][video_id]["skipOnliveNotify"]:
                    onlive_message = text.get_onlive_message(video_id=video_id).format(video_id=video_id, channel_name=channel_name, channel_id=channel_id)
                    if const.ENABLED_MODULES_ONLIVE["discord"]:
                        discord.send(const.DISCORD_WEBHOOK_URL_ONLIVE, onlive_message, version=const.VERSION)
                        fetched[channel_name][video_id]["skipOnliveNotify"] = True
                    if const.ENABLED_MODULES_ONLIVE["telegram"]:    
                        telegram.send(const.TELEGRAM_BOT_TOKEN_ONLIVE, const.TELEGRAM_CHAT_ID_ONLIVE, onlive_message)
                        fetched[channel_name][video_id]["skipOnliveNotify"] = True
                    if const.ENABLED_MODULES_ONLIVE["pushalert"]:
                        pushalert.onlive(video_data)
                        fetched[channel_name][video_id]["skipOnliveNotify"] = True
                    if const.ENABLED_MODULES_ONLIVE["fcm"]:
                        fcm.onlive(video_data)
                        fetched[channel_name][video_id]["skipOnliveNotify"] = True

                utils.log(f"[{channel_name}] Saving {m3u8_id}...")

                fetched[channel_name][video_id]["fregments"][m3u8_id] = {
                    "file": filepath,
                    "create_time": time.time()
                }

                if len(fetched[channel_name][video_id]["fregments"]) > 1:
                    if "multiManifestNotify" not in fetched[channel_name][video_id]:
                        fetched[channel_name][video_id]["multiManifestNotify"] = 1
                    if len(fetched[channel_name][video_id]["fregments"]) > fetched[channel_name][video_id]["multiManifestNotify"] and text.MULTI_MANIFEST_MESSAGE:
                        fetched[channel_name][video_id]["multiManifestNotify"] = len(fetched[channel_name][video_id]["fregments"])

                        files = [fetched[channel_name][video_id]["fregments"][m3u8_id]["file"] for m3u8_id in fetched[channel_name][video_id]["fregments"]]
                        message = text.MULTI_MANIFEST_MESSAGE.format(video_id=video_id, channel_name=channel_name, channel_id=channel_id)

                        utils.notify(message, files)

                        utils.log(f" {message}")

                save()
            else:
                utils.log(f"[{channel_name}] Not on live.")

            utils.log(f" Sleeping for {const.TIME_BETWEEN_CHECK} secs...")
            time.sleep(const.TIME_BETWEEN_CHECK)
except KeyboardInterrupt:
    utils.log(" Forced stop.")
finally:
    expiry_task.stop()

    if const.CHAT_DIR:
        chat_expiry_task.stop()
        for video_id in chats:
            chats[video_id].stop()

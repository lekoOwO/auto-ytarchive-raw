import json
import time
import os

import utils
import getm3u8
import getjson

import const

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
    for channel_name in fetched:
        for video_id in fetched[channel_name]:
            for m3u8_id in fetched[channel_name][video_id]:
                if time.time() - fetched[channel_name][video_id][m3u8_id]["create_time"] > const.EXPIRY_TIME:
                    utils.log(f"[{channel_name}] {m3u8_id} has expired. Clearing...")

                    try:
                        os.remove(fetched[channel_name][video_id][m3u8_id]["file"])
                    except:
                        utils.warn(f"[{channel_name}] Error occurs when deleting {m3u8_id}. Ignoring...")

                    fetched[channel_name][video_id].pop(m3u8_id)
            if not fetched[channel_name][video_id]:
                utils.log(f"[{channel_name}] {video_id} has all gone. Clearing...")
                fetched[channel_name].pop(video_id)
    save()
try:
    expiry_task = utils.RepeatedTimer(const.TIME_BETWEEN_CLEAR, clear_expiry)

    while True:
        for channel_name, channel_id in CHANNELS.items():
            is_live = utils.is_live(channel_id)
            if is_live:
                utils.log(f"[{channel_name}] On live!")

                video_url = is_live

                video_id = getjson.get_youtube_id(video_url)
                m3u8_url = getm3u8.get_m3u8(video_url)
                m3u8_id = getm3u8.get_m3u8_id(m3u8_url)

                if channel_name not in fetched:
                    fetched[channel_name] = {
                        video_id: {}
                    }
                
                if video_id not in fetched[channel_name]:
                    fetched[channel_name][video_id] = {}

                filepath = os.path.join(const.BASE_JSON_DIR, f"{m3u8_id}.json")
                getjson.get_json(video_url, filepath)

                utils.log(f"[{channel_name}] Saving {m3u8_id}...")

                fetched[channel_name][video_id][m3u8_id] = {
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
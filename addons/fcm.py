import const
import text
import utils

import urllib.request, urllib.parse

def onlive(video_id, channel_id, channel_name):
    data = {
        'title': text.FCM_TITLE.format(video_id=video_id, channel_name=channel_name, channel_id=channel_id),
        "message": text.FCM_MESSAGE.format(video_id=video_id, channel_name=channel_name, channel_id=channel_id),
        "click_action": f"https://youtu.be/{video_id}"
    }
    if const.FCM_ICON:
        data["icon"] = const.FCM_ICON

    data = json.dumps(data).encode()

    req = urllib.request.Request(url="https://fcm.googleapis.com/fcm/send", method="POST", data=data)
    req.add_header('Content-Type', 'application/json')
    
    req.add_header("Authorization", f"key={const.FCM_API_KEY}")

    try:
        return utils.urlopen(req)
    except:
        return
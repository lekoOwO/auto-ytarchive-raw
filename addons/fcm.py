import const
import text
import utils
import json

import urllib.request, urllib.parse

def onlive(video_data):
    if "thumbnailUrl" in video_data['metadata']:
        image = video_data['metadata']["thumbnailUrl"]
    else:
        image = video_data['metadata']["thumbnail"]

    data = {
        "to": const.FCM_TARGET,
        "validateOnly": False,
        "notification": {
            'title': text.FCM_TITLE.format(**video_data["metadata"]),
            "body": text.FCM_MESSAGE.format(**video_data["metadata"]),
            "click_action": f"https://www.youtube.com/watch?v={video_data['metadata']['id']}",
            "image": image
        }
    }

    if const.FCM_ICON:
        data["notification"]["icon"] = const.FCM_ICON
    else:
        data["notification"]["icon"] = utils.get_avatar(video_data['metadata']["channelURL"])


    data = json.dumps(data).encode()

    req = urllib.request.Request(
        url="https://fcm.googleapis.com/fcm/send", method="POST", data=data)
    req.add_header('Content-Type', 'application/json')

    req.add_header("Authorization", f"key={const.FCM_API_KEY}")

    try:
        return utils.urlopen(req)
    except:
        return
import const
import text
import utils

import urllib.request, urllib.parse

def onlive(video_id, channel_id, channel_name):
    data = {
        'title': text.PUSHALERT_TITLE.format(video_id=video_id, channel_name=channel_name, channel_id=channel_id),
        "message": text.PUSHALERT_MESSAGE.format(video_id=video_id, channel_name=channel_name, channel_id=channel_id),
        "url": f"https://youtu.be/{video_id}"
    }
    if const.PUSHALERT_ICON:
        data["icon"] = const.PUSHALERT_ICON

    data = urllib.parse.urlencode(data).encode()

    req = urllib.request.Request(url="https://api.pushalert.co/rest/v1/send", data=data)
    req.add_header("Authorization", f"api_key={const.PUSHALERT_API_KEY}")

    return utils.urlopen(req)
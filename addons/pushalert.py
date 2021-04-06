import const
import text
import utils

import urllib.request, urllib.parse

def onlive(video_data):
    data = {
        'title': text.PUSHALERT_TITLE.format(**video_data["metadata"]),
        "message": text.PUSHALERT_MESSAGE.format(**video_data["metadata"]),
        "url": f"https://youtu.be/{video_data['metadata']['id']}"
    }
    if const.PUSHALERT_ICON:
        data["icon"] = const.PUSHALERT_ICON
    else:
        data["icon"] = utils.get_avatar(video_data['metadata']["channelURL"])

    data = urllib.parse.urlencode(data).encode()

    req = urllib.request.Request(url="https://api.pushalert.co/rest/v1/send", data=data)
    req.add_header("Authorization", f"api_key={const.PUSHALERT_API_KEY}")

    try:
        return utils.urlopen(req)
    except:
        return
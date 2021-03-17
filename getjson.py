import urllib.request
import urllib.parse
import re
from html.parser import HTMLParser
import base64
import datetime
import json

VERSION = "1.1"

PRIORITY = {
    "VIDEO": [
        337, 315, 266, 138, # 2160p60
        313, 336, # 2160p
        308, # 1440p60
        271, 264, # 1440p
        335, 303, 299, # 1080p60
        248, 169, 137, # 1080p
        334, 302, 298, # 720p60
        247, 136 # 720p
    ],
    "AUDIO": [
        251, 141, 171, 140, 250, 249, 139
    ]
}

def get_youtube_id(url):
    try:
        return re.search(r'^.*(?:(?:youtu\.be\/|v\/|vi\/|u\/\w\/|embed\/)|(?:(?:watch)?\?v(?:i)?=|\&v(?:i)?=))([^#\&\?]*).*', url).group(1)
    except:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode()
            regex = r'<meta itemprop="videoId" content="(.+?)">'
            result = re.search(regex, html).group(1)

            return result

def get_youtube_video_info(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    with urllib.request.urlopen(url) as response:
        html = response.read().decode()

        return {
            "title": re.search(r'<meta name="title" content="(.+?)">', html).group(1),
            "id": video_id,
            "channelName": re.search(r'<link itemprop="name" content="(.+?)">', html).group(1),
            "channelURL": re.search(r'<link itemprop="url" href="(.+?)">', html).group(1),
            "description": re.search(r'"description":{"simpleText":"(.+?)"},', html).group(1).replace("\\n", "\n"),
            "thumbnail": get_image(f"https://i3.ytimg.com/vi/{video_id}/maxresdefault.jpg")
        }

def get_image(url):
    with urllib.request.urlopen(url) as response:
        data = response.read()
        b64 = base64.b64encode(data).decode()

        return f"data:image/jpeg;base64,{b64}"

def get_json(video_url, file=None):
    video_id = get_youtube_id(video_url)

    info_url = f"https://www.youtube.com/get_video_info?video_id={video_id}"
    info_req = urllib.request.Request(
        info_url, 
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        }
    )
    with urllib.request.urlopen(info_req) as response:
        data = response.read().decode()
        data = urllib.parse.unquote(data)

        match = re.findall(r'"itag":(\d+),"url":"([^"]+)"', data)
        match = dict(x for x in match)

        best = {
            "video": None,
            "audio": None,
            "metadata": get_youtube_video_info(video_id),
            "version": VERSION,
            "createTime": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        }

        for itag in PRIORITY["VIDEO"]:
            itag = str(itag)
            if itag in match:
                best["video"] = {
                    itag: match[itag].replace("\\u0026", "\u0026")
                }
                break
        for itag in PRIORITY["AUDIO"]:
            itag = str(itag)
            if itag in match:
                best["audio"] = {
                    itag: match[itag].replace("\\u0026", "\u0026")
                }
                break
        if file is not None:
            with open(file, "w", encoding="utf8") as f:
                json.dump(best, f, indent=4, ensure_ascii=False)
        return best

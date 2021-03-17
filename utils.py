import urllib.request
import re
import time

from threading import Timer

import const
import utils

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

def urlopen(url, retry = 0):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        if e.code == 503:
            if retry < const.HTTP_RETRY:
                utils.warn(f" Get {e.code} Error. Trying {retry}/{const.HTTP_RETRY}...")
                time.sleep(1)
                return urlopen(url, retry+1)
            else:
                raise e
        else:
            raise e


def is_live(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    with urlopen(url) as response:
        html = response.read().decode()

        try:
            og_url = re.search(r'<meta property="og:url" content="(.+?)">', html).group(1)
        except AttributeError:
            og_url = re.search(r'<link rel="canonical" href="(.+?)">', html).group(1)

        if "watch?v=" in og_url:
            if "LIVE_STREAM_OFFLINE" in html:
                return False # Scheduled
            return og_url
        elif "/channel/" in og_url or "/user/" in og_url:
            return False
        else:
            raise RuntimeError(f"Something weird happened on checking Live for {channel_id}...")

def is_privated(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    with urlopen(url) as response:
        html = response.read().decode()

        return "Q0FBU0FnZ0E=" in html

def log(msg):
    print(f"[INFO]{msg}")

def warn(msg):
    print(f"[WARN]{msg}")
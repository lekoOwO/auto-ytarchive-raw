import urllib.request
import urllib.parse
import http.cookiejar
import re
import time
from enum import Enum, auto
import os
import json

import functools
import http.client

import ipaddress
import random

import threading
from addons import discord
from addons import telegram

import const

def log(msg):
    print(f"[INFO]{msg}")


def warn(msg):
    print(f"[WARN]{msg}")


class PlayabilityStatus(Enum):
    PRIVATED = auto()
    COPYRIGHTED = auto()
    REMOVED = auto()
    MEMBERS_ONLY = auto()
    OFFLINE = auto()
    OK = auto()
    ON_LIVE = auto()
    UNKNOWN = auto()
    LOGIN_REQUIRED = auto()


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class BoundHTTPHandler(urllib.request.HTTPHandler):
    def __init__(self, *args, source_address=None, **kwargs):
        urllib.request.HTTPHandler.__init__(self, *args, **kwargs)
        self.http_class = functools.partial(http.client.HTTPConnection,
                source_address=source_address)

    def http_open(self, req):
        return self.do_open(self.http_class, req)


class BoundHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, *args, source_address=None, **kwargs):
        urllib.request.HTTPSHandler.__init__(self, *args, **kwargs)
        self.https_class = functools.partial(http.client.HTTPSConnection,
                source_address=source_address)

    def https_open(self, req):
        return self.do_open(self.https_class, req,
                context=self._context, check_hostname=self._check_hostname)


def get_random_line(filepath: str) -> str:
    file_size = os.path.getsize(filepath)
    with open(filepath, 'rb') as f:
        while True:
            pos = random.randint(0, file_size)
            if not pos:  # the first line is chosen
                return f.readline().decode()  # return str
            f.seek(pos)  # seek to random position
            f.readline()  # skip possibly incomplete line
            line = f.readline()  # read next (full) line
            if line:
                return line.decode()
            # else: line is empty -> EOF -> try another position in next iteration


def is_ip(ip):
    try:
        ip = ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def get_pool_ip():
    if const.IP_POOL:
        if os.path.isfile(const.IP_POOL):
            for _ in range(3): # Retry for 3 times.
                ip = get_random_line(const.IP_POOL).rstrip().lstrip()
                if is_ip(ip):
                    return ip
    return None


def urlopen(url, retry=0, source_address="random", use_cookie=False):
    try:
        handlers = []

        if source_address == "random":
            source_address = get_pool_ip()
        if not is_ip(source_address):
            source_address = None
        
        if use_cookie:
            if hasattr(const, "COOKIE") and const.COOKIE and os.path.isfile(const.COOKIE):
                cj = http.cookiejar.MozillaCookieJar()
                cj.load(const.COOKIE)
                cookie_handler = urllib.request.HTTPCookieProcessor(cj)
                handlers.append(cookie_handler)
            
        if source_address:
            log(f" Using IP: {source_address}")
            scheme = "https"
            if type(url) == str:
                scheme = urllib.parse.urlsplit(url).scheme
            elif isinstance(url, urllib.request.Request):
                scheme = urllib.parse.urlsplit(url.full_url).scheme

            handler = (BoundHTTPHandler if scheme == "http" else BoundHTTPSHandler)(source_address=(source_address, 0))
            handlers.append(handler)
        
        if handlers:
            return urllib.request.build_opener(*handlers).open(url)
        else:
            return urllib.request.urlopen(url)
    except http.client.IncompleteRead as e:
        if retry < const.HTTP_RETRY:
            warn(f" Get IncompleteRead Error. Trying {retry+1}/{const.HTTP_RETRY}...")
            return urlopen(url, retry+1, get_pool_ip() if source_address else None, use_cookie)
        else:
            raise e
    except urllib.error.HTTPError as e:
        if e.code == 503:
            if retry < const.HTTP_RETRY:
                warn(f" Get {e.code} Error. Trying {retry+1}/{const.HTTP_RETRY}...")
                time.sleep(1)
                return urlopen(url, retry+1, get_pool_ip() if source_address else None, use_cookie)
            else:
                raise e
        else:
            raise e
    except urllib.error.URLError as e:
        if retry < const.HTTP_RETRY:
            warn(f" Get urllib.error.URLError Error. Trying {retry+1}/{const.HTTP_RETRY}...")
            return urlopen(url, retry+1, get_pool_ip() if source_address else None, use_cookie)
        else:
            raise e


def is_live(channel_id, use_cookie=False):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    with urlopen(url, use_cookie=use_cookie) as response:
        html = response.read().decode()

        try:
            og_url = re.search(
                r'<meta property="og:url" content="(.+?)">', html).group(1)
        except AttributeError:
            try:
                og_url = re.search(
                    r'<link rel="canonical" href="(.+?)">', html).group(1)
            except:
                return is_live(channel_id, use_cookie=use_cookie) # Try again, sth weird happened

        if "watch?v=" in og_url:
            if 'hlsManifestUrl' not in html:
                if '"status":"LOGIN_REQUIRED"' in html:
                    if use_cookie:
                        return False  # No permission
                    else:
                        # Try again with cookie
                        return is_live(channel_id, use_cookie=True)
                return False  # No stream found
            return og_url  # Stream found
        elif "/channel/" in og_url or "/user/" in og_url:
            return False
        else:
            warn(
                f" Something weird happened on checking Live for {channel_id}...")
            return False

# 2021.5.7 Youtube chokes for PlayabilityStatus.REMOVED
# if PlayabilityStatus.REMOVED, we now check 3 times for accuracy.

def get_video_status(video_id):
    def _get_video_status(video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        req = urllib.request.Request(url)
        req.add_header('Accept-Language', 'en-US,en;q=0.5')

        with urlopen(req) as response:
            html = response.read().decode()

            if '"offerId":"sponsors_only_video"' in html:
                return PlayabilityStatus.MEMBERS_ONLY
            elif '"status":"UNPLAYABLE"' in html:
                return PlayabilityStatus.COPYRIGHTED
            elif '"status":"LOGIN_REQUIRED"' in html:
                return PlayabilityStatus.PRIVATED
            elif '"status":"ERROR"' in html:
                return PlayabilityStatus.REMOVED
            elif '"status":"OK"' in html:
                if 'hlsManifestUrl' in html:
                    return PlayabilityStatus.ON_LIVE
                return PlayabilityStatus.OK
            elif '"status":"LIVE_STREAM_OFFLINE"' in html:
                return PlayabilityStatus.OFFLINE
            elif '"status":"LOGIN_REQUIRED"' in html:
                return PlayabilityStatus.LOGIN_REQUIRED
            else:
                with open(os.path.join(const.LOGS_DIR, f"{video_id}.html"), "w", encoding="utf8") as f:
                    f.write(html)
                return PlayabilityStatus.UNKNOWN
    
    status = _get_video_status(video_id)
    if status is PlayabilityStatus.REMOVED:
        for _ in range(3):
            tmp = _get_video_status(video_id)
            if tmp is not PlayabilityStatus.REMOVED:
                return tmp
    return status


def notify(message, files=None):
    if const.ENABLED_MODULES["discord"]:
        threading.Thread(target=discord.send, args=(const.DISCORD_WEBHOOK_URL, message), kwargs={
            "version": const.VERSION,
            "files": files if const.DISCORD_SEND_FILES else None
        }, daemon=True).start()
    if const.ENABLED_MODULES["telegram"]:
        if const.TELEGRAM_SEND_FILES:
            threading.Thread(target=telegram.send_files, args=(const.TELEGRAM_BOT_TOKEN, const.TELEGRAM_CHAT_ID, message, files), daemon=True).start()
        else:
            threading.Thread(target=telegram.send, args=(const.TELEGRAM_BOT_TOKEN, const.TELEGRAM_CHAT_ID, message), daemon=True).start()

def get_avatar(url):
    regex = r'"avatar":{"thumbnails":(\[{[^\]]+?\])}'
    with urlopen(url) as resp:
        html = resp.read().decode()
        result = re.findall(regex, html)

    result = [json.loads(x) for x in result]
    result = [item for sublist in result for item in sublist]
    result = max(result, key=lambda x: x['width'])
    result = result['url']
    return result
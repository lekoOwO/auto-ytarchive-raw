import urllib.request, urllib.parse
import re
import time
from enum import Enum, auto
import os

import functools
import http.client

import ipaddress
import random

from threading import Timer

import const

if const.CHAT_COMPRESS == "brotli":
    import brotli
    import tempfile
elif const.CHAT_COMPRESS == "zstd":
    import zstandard
    import tempfile


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
    UNKNOWN = auto()

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
            for _ in range(3): 
                ip = get_random_line(const.IP_POOL).rstrip().lstrip()
                if is_ip(ip):
                    return ip
    return None

def urlopen(url, retry=0, source_address="random"):
    try:
        if source_address == "random":
            source_address = get_pool_ip()
        if not is_ip(source_address):
            source_address = None
        if source_address:
            log(f" Using IP: {source_address}")
            schema = "https"
            if type(url) == str:
                schema = urllib.parse.urlsplit(url).scheme
            elif isinstance(url, urllib.request.Request):
                schema = urllib.parse.urlsplit(url.full_url).scheme

            handler = (BoundHTTPHandler if schema == "http" else BoundHTTPSHandler)(source_address=(source_address, 0))
            opener = urllib.request.build_opener(handler)
            return opener.open(url)
        else:
            return urllib.request.urlopen(url)
    except http.client.IncompleteRead as e:
        if retry < const.HTTP_RETRY:
            warn(f" Get IncompleteRead Error. Trying {retry+1}/{const.HTTP_RETRY}...")
            return urlopen(url, retry+1, get_pool_ip() if source_address else None)
        else:
            raise e
    except urllib.error.HTTPError as e:
        if e.code == 503:
            if retry < const.HTTP_RETRY:
                warn(f" Get {e.code} Error. Trying {retry+1}/{const.HTTP_RETRY}...")
                time.sleep(1)
                return urlopen(url, retry+1, get_pool_ip() if source_address else None)
            else:
                raise e
        else:
            raise e
    except urllib.error.URLError as e:
        if retry < const.HTTP_RETRY:
            warn(f" Get urllib.error.URLError Error. Trying {retry+1}/{const.HTTP_RETRY}...")
            return urlopen(url, retry+1, get_pool_ip() if source_address else None)
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
            if 'hlsManifestUrl' not in html:
                return False # No stream found
            return og_url
        elif "/channel/" in og_url or "/user/" in og_url:
            return False
        else:
            warn(f" Something weird happened on checking Live for {channel_id}...")
            return False

def get_video_status(video_id):
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
            return PlayabilityStatus.OK
        elif '"status":"LIVE_STREAM_OFFLINE"' in html:
            return PlayabilityStatus.OFFLINE
        else:
            with open(os.path.join(const.LOGS_DIR, f"{video_id}.html"), "w", encoding="utf8") as f:
                f.write(html)
            return PlayabilityStatus.UNKNOWN

if const.CHAT_COMPRESS == "brotli":
    def compress_file(file):
        with open(file, encoding="utf8") as f:
            compressor = brotli.Compressor(mode=brotli.BrotliEncoderMode.TEXT)
            with tempfile.NamedTemporaryFile(prefix=(os.path.basename(file)+"."), suffix=".br", delete=False) as l:
                for line in f:
                    data = line.encode()
                    data = compressor.compress(data)
                    l.write(compressor.flush())
                l.write(compressor.finish())
                return l.name
elif const.CHAT_COMPRESS == "zstd":
    def compress_file(file):
        cctx = zstandard.ZstdCompressor()
        with open(file, "rb") as ifh, tempfile.NamedTemporaryFile(prefix=(os.path.basename(file)+"."), suffix=".zst", delete=False) as ofh:
            cctx.copy_stream(ifh, ofh)
            return ofh.name
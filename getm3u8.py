import urllib.request
import re

def get_m3u8(url):
    with urllib.request.urlopen(url) as response:
        html = response.read().decode()
        regex = r"hlsManifestUrl\":\"([^\"]+)"
        result = re.search(regex, html).group(1)

        return result

def get_m3u8_id(m3u8_url):
    regex = r"/id/(.+?)/"
    result = re.search(regex, m3u8_url).group(1)

    return result
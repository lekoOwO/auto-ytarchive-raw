import urllib.request
import re
import utils

def get_m3u8(url):
    with utils.urlopen(url) as response:
        html = response.read().decode()
        regex = r"hlsManifestUrl\":\"([^\"]+)"
        result = re.search(regex, html).group(1)

        return result

def get_m3u8_id(m3u8_url):
    regex = r"/id/(.+?)/"
    result = re.search(regex, m3u8_url).group(1)

    # sometimes youtube sends the ids in the format
    # `<video id>.<number>~<random numbers>` so just
    # ignore the random part and keep the relevant ones
    result = result.split("~")[0]

    return result

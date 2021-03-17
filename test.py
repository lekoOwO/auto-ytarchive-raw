import urllib.request
import re

def get_m3u8(url):
    with urllib.request.urlopen(url) as response:
        html = response.read().decode()
        regex = r"hlsManifestUrl\":\"([^\"]+)"
        result = re.search(regex, html).group(1)

        return result

print(get_m3u8("https://www.youtube.com/watch?v=SAWk7m9xEFY"))
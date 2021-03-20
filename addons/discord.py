import json
import urllib.request

import addons.addon_utils as utils

def send(webhook_url, message, files=None, version="1.0"):
    payload = [
        ("payload_json", json.dumps({
            "content": message
        }))
    ]

    if files:
        for i in range(len(files)):
            payload.append((f"file{i}", f"f'{files[i]}'"))

    content_type, payload = utils.encode_multipart_formdata(payload)

    req = urllib.request.Request(webhook_url, method="POST")
    req.add_header('Content-Type', content_type)
    req.add_header('User-Agent', f'Auto YTArchive Raw {version}')

    return urllib.request.urlopen(req, data=payload)
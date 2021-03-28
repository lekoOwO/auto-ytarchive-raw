import json
import urllib.request

import addons.addon_utils as utils
import const

if const.CHAT_COMPRESS:
    import pathlib
    import os

def send(webhook_url, message, files=None, version="1.0"):
    payload = [
        ("payload_json", json.dumps({
            "content": message
        }))
    ]

    if const.CHAT_COMPRESS:
        compressed = []

    if files:
        for i in range(len(files)):
            if const.CHAT_COMPRESS and pathlib.Path(files[i]).suffix == ".chat":
                filename = utils.compress_file(files[i])
                compressed.append(filename)
                payload.append((f"file{i}", f"f'{filename}'"))
            else:
                payload.append((f"file{i}", f"f'{files[i]}'"))

    content_type, payload = utils.encode_multipart_formdata(payload)

    req = urllib.request.Request(webhook_url, method="POST")
    req.add_header('Content-Type', content_type)
    req.add_header('User-Agent', f'Auto YTArchive Raw {version}')

    with urllib.request.urlopen(req, data=payload) as f:
        status = f.getcode()
        if const.CHAT_COMPRESS:
            for x in compressed:
                try:
                    os.remove(x)
                except:
                    pass
        return status
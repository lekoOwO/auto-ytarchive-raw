import json
import urllib.request
import tempfile
import os

import addons.addon_utils as utils
import const

if const.BROTLI_COMPRESS:
    import pathlib

def send(token, chat_id, message):
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "markdown"
    }

    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", method="POST")
    req.add_header('Content-Type', 'application/json')
    payload = json.dumps(payload).encode()

    return urllib.request.urlopen(req, data=payload)

def send_files(token, chat_id, message, files):
    if len(files) > 1:
        return send_multi_files(token, chat_id, message, files)

    payload = [
        ("chat_id", chat_id),
        ("caption", message),
        ("parse_mode", "markdown")
    ]

    if const.BROTLI_COMPRESS and pathlib.Path(files[0]).suffix == ".chat":
        compressed = utils.compress_file(files[0])
        payload.append(("document", f"f'{compressed}'"))
    else:
        payload.append(("document", f"f'{files[0]}'"))
    content_type, payload = utils.encode_multipart_formdata(payload)

    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendDocument", method="POST")
    req.add_header('Content-Type', content_type)

    with urllib.request.urlopen(req, data=payload) as f:
        status = f.getcode()
        if const.BROTLI_COMPRESS and pathlib.Path(files[0]).suffix == ".chat":
            try:
                os.remove(compressed)
            except:
                pass
        return status



def send_multi_files(token, chat_id, message, files):
    payload = [
        ("chat_id", chat_id),
        ("allow_sending_without_reply", "true")
    ]

    media = []
    if const.BROTLI_COMPRESS:
        compressed = []

    for i in range(len(files)):
        if const.BROTLI_COMPRESS and pathlib.Path(files[i]).suffix == ".chat":
            filename = utils.compress_file(files[i])
            compressed.append(filename)
            payload.append((f"file{i}", f"f'{filename}'"))
        else:
            payload.append((f"file{i}", f"f'{files[i]}'"))

        media.append({
            "type": "document",
            "media": f"attach://file{i}",
            "caption": message if i == (len(files) - 1) else "",
            "parse_mode": "markdown"
        })
    
    payload.append(("media", json.dumps(media)))
    content_type, payload = utils.encode_multipart_formdata(payload)
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMediaGroup", method="POST")
    req.add_header('Content-Type', content_type)

    with urllib.request.urlopen(req, data=payload) as f:
        status = f.getcode()
        if const.BROTLI_COMPRESS:
            for x in compressed:
                try:
                    os.remove(x)
                except:
                    pass
        return status
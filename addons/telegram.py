import json
import urllib.request
from zipfile import ZipFile
import tempfile
import os

import addons.addon_utils as utils

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
    payload = [
        ("chat_id", chat_id),
        ("caption", message),
        ("parse_mode", "markdown")
    ]

    if len(files) > 1:
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "archive.zip")
            with ZipFile(zip_path, 'w') as zip_obj:
                for x in files:
                    zip_obj.write(x)
            payload.append(("document", f"f'{zip_path}'"))

            content_type, payload = utils.encode_multipart_formdata(payload)
    else:
        payload.append(("document", f"f'{files[0]}'"))
        content_type, payload = utils.encode_multipart_formdata(payload)

    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendDocument", method="POST")
    req.add_header('Content-Type', content_type)

    return urllib.request.urlopen(req, data=payload)
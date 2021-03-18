import json
import urllib.request

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
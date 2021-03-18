import json
import urllib.request

def send(webhook_url, message):
    payload = {
        "content": message
    }

    req = urllib.request.Request(webhook_url, method="POST")
    req.add_header('Content-Type', 'application/json')
    payload = json.dumps(payload).encode()

    return urllib.request.urlopen(req, data=payload)
# auto-ytarchive-raw

## Usage

### Docker

This usage guide is for the [Docker](https://www.docker.com/) image.
If you do not have or haven't heard of Docker, please see the [Docker](https://www.docker.com/) website.

For basic usage, simply run the following command:
```bash
docker run \
  -d `#runs the container in the background` \
  -v /path/to/channels.json:/app/config.json `# Mounts the channels.json file. For usage, reference below` \
  -v /path/to/json/:/app/json/ `# A folder that will hold the output JSON files` \
  -v /path/to/const.py:/app/const.py `#(OPTIONAL) mounts the const.py. For usage, reference below` \
  -v /path/to/text.py:/app/text.py `#(OPTIONAL) mounts the text.py. For usage, reference below` \
```

[Channel configuration file example](channels.example.yml)

(OPTIONAL) [Const.py example](const.example.py)

(OPTIONAL) [Text.py example](text.example.py)
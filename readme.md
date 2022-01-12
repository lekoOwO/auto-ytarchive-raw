# auto-ytarchive-raw

## Usage

### Docker

This usage guide is for the [Docker](https://www.docker.com/) image.
If you do not have or haven't heard of Docker, please see the [Docker](https://www.docker.com/) website.

#### Docker-compose

Modify the `docker-compose.yml` file to your liking, then run `docker-compose up` to start the container.

#### Docker run
For basic usage, simply modify and run the following command:
```bash
docker run \
  -it `#Makes sure the logs are captured` \
  -d `#Runs the container in the background` \
  -v /path/to/channels.json:/app/config.json `# Mounts the channels.json file. For usage, reference below` \
  -v /path/to/jsons/:/app/jsons/ `# A folder that will hold the output JSONS files` \
  -v /path/to/const.py:/app/const.py `#(OPTIONAL) Mounts the const.py. For usage, reference below` \
  -v /path/to/text.py:/app/text.py `#(OPTIONAL) Mounts the text.py. For usage, reference below` \
  --restart=unless-stopped `# Restarts the container when it crashes` \
  ghcr.io/lekoOwO/auto-ytarchive-raw:master
```
#### Config files

When an optional is left out, the example below will be used.

[Channel configuration file example](channels.example.yml)

(OPTIONAL) [Const.py example](const.example.py)

(OPTIONAL) [Text.py example](text.example.py)
FROM python:3-alpine
WORKDIR /app
COPY . .

# Copy the examples to the app directory. When docker run is called with -v
# it overwrites the files in the container. So it's perfectly fine to copy
# the examples to the app directory.
COPY ./const.py.example ./const.py
COPY ./text.py.example ./text.py

CMD ["python", "index.py"]

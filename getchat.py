from chat_downloader import ChatDownloader
import json
import threading
import os
import time

import const
import utils

class ChatArchiver:
    def __init__(self, url, output_file):
        self.url = url
        self.output_file = output_file
        with open(self.output_file, "a+", encoding="utf8") as f:
            f.write(f"# Time: {time.time()}, URL: {url}\n")

        self.chat = ChatDownloader().get_chat(url, message_groups='all', inactivity_timeout=const.CHAT_INACTIVITY_DURATION)
        self.timer = utils.RepeatedTimer(const.CHAT_BUFFER_TIME, self.__save_chat)
        self.buffer = [[], []]
        self.buffer_index = 0
        self.is_stop = False

        self.download_task = threading.Thread(target=self.__download_chat, daemon=True)
        self.download_task.start()

    def __save_chat(self):
        old_buffer_index = self.buffer_index
        self.buffer_index = (self.buffer_index + 1) % 2

        with open(self.output_file, "a+", encoding="utf8") as f:
            for chat in self.buffer[old_buffer_index]:
                json.dump(chat, f, ensure_ascii=False)
                f.write("\n")

        self.buffer[old_buffer_index] = []
    
    def __download_chat(self):
        for chat in self.chat:
            self.buffer[self.buffer_index].append(chat)

        self.is_stop = True
        self.timer.stop()
        self.__save_chat()

    def is_finished(self):
        return self.is_stop

    def stop(self):
        self.is_stop = True
        self.timer.stop()
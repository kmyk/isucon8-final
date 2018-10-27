"""
ISULOG client
"""
from __future__ import annotations

import json
import time
import urllib.parse
import queue
import random
import threading

import requests


class IsuLogger:
    def __init__(self, load_setting):
        self.load_setting = load_setting
        self.que = queue.Queue()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
        with open('/home/isucon/foo', 'a') as fh:
            fh.write('IsuLogger.__init__\n')

    def send(self, tag, data):
        with open('/home/isucon/foo', 'a') as fh:
            fh.write('IsuLogger.send\n')
        self.que.put((tag, data))

    def _request(self, path, data):
        url = urllib.parse.urljoin(self.endpoint, path)
        body = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.appID,
        }

        res = requests.post(url, data=body, headers=headers)
        res.raise_for_status()
        with open('/home/isucon/foo', 'a') as fh:
            fh.write('IsuLogger._request\n')

    def run(self):
        while True:
            with open('/home/isucon/foo', 'a') as fh:
                fh.write('IsuLogger.run/loop\n')
            bulk = []
            while not self.que.empty():
                tag, data = self.que.get()
                bulk += [ {
                    "tag": tag,
                    "time": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                    "data": data,
                } ]
            if bulk:
                self.endpoint, self.appID = self.load_setting()
                self._request('/send_bulk', bulk)
            time.sleep(3 + random.random())

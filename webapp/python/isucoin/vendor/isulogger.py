"""
ISULOG client
"""
from __future__ import annotations

import json
import time
import urllib.parse

import threading
from queue import Queue
import time

import requests

from isucoin.db_manage import get_dbconn, transaction

import sys

LOG_ENDPOINT = "log_endpoint"
LOG_APPID = "log_appid"

class IsuLogger:
    def __init__(self):
        self.stop_event = threading.Event()
        self.queue = Queue()
        self.thread = threading.Thread(target=self._send_bulk)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()

    def _send_bulk(self):
        while not self.stop_event.is_set():
            logs = []
            while not self.queue.empty():
                logs.append(self.queue.get())
            if logs:
                self._request("/send_bulk", logs)
            time.sleep(1)

    def send(self, tag, data):
        self.queue.put(
            {
                "tag": tag,
                "time": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "data": data,
            },
        )


    def _get_setting(self, db, k: str) -> str:
        print("[info] GET SETTING")
        cur = db.cursor()
        cur.execute("SELECT val FROM setting WHERE name = %s", (k,))
        return cur.fetchone()[0]

    def _request(self, path, data):
        try:
            print("[info] SEND LOGS")
            db = get_dbconn()
            endpoint = self._get_setting(db, LOG_ENDPOINT)
            appID = self._get_setting(db, LOG_APPID)
            url = urllib.parse.urljoin(endpoint, path)
            body = json.dumps(data)
            print(url)
            print(body)
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + appID,
            }

            res = requests.post(url, data=body, headers=headers)
            res.raise_for_status()
        except Exception as e:
            print("ERROR")
            print("Unexpected error:", e)
            raise

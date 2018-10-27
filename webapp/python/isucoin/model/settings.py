from __future__ import annotations

import isubank
import isulogger
import time

from isucoin.db import get_new_dbconn


BANK_ENDPOINT = "bank_endpoint"
BANK_APPID = "bank_appid"
LOG_ENDPOINT = "log_endpoint"
LOG_APPID = "log_appid"

_isubank = None
_isubank_timestamp = 0


def set_setting(db, k: str, v: str):
    cur = db.cursor()
    cur.execute(
        "INSERT INTO setting (name, val) VALUES (%s, %s) ON DUPLICATE KEY UPDATE val = VALUES(val)",
        (k, v),
    )


def get_setting(db, k: str) -> str:
    cur = db.cursor()
    cur.execute("SELECT val FROM setting WHERE name = %s", (k,))
    return cur.fetchone()[0]


class SettingLoader(object):
    def __init__(self, db, endpoint_key: str, appid_key: str):
        self.db = db
        self.endpoint_key = endpoint_key
        self.appid_key = appid_key

    def __call__(self):
        endpoint = get_setting(self.db, self.endpoint_key)
        appid = get_setting(self.db, self.appid_key)
        return (endpoint, appid)


def get_isubank(db):
    global _isubank, _isubank_timestamp
    if _isubank_timestamp + 3 < time.time():
        _isubank = None
    if _isubank is None:
        _isubank_timestamp = time.time()
        endpoint = get_setting(db, BANK_ENDPOINT)
        appid = get_setting(db, BANK_APPID)
        _isubank = isubank.IsuBank(endpoint, appid)
    return _isubank


_logger = isulogger.IsuLogger(SettingLoader(get_new_dbconn(), LOG_ENDPOINT, LOG_APPID))

def send_log(db, tag, v):
    global _logger
    _logger.send(tag, v)

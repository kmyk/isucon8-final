from __future__ import annotations

import isubank
import isulogger
import time


BANK_ENDPOINT = "bank_endpoint"
BANK_APPID = "bank_appid"
LOG_ENDPOINT = "log_endpoint"
LOG_APPID = "log_appid"

_isubank = None
_isubank_timestamp = 0
_logger = None
_logger_timestamp = 0


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


def get_logger(db):
    global _logger, _logger_timestamp
    if _logger_timestamp + 3 < time.time():
        _logger = None
    if _logger is None:
        _logger_timestamp = time.time()
        endpoint = get_setting(db, LOG_ENDPOINT)
        appid = get_setting(db, LOG_APPID)
        _logger = isulogger.IsuLogger(endpoint, appid)
    return _logger


def send_log(db, tag, v):
    logger = get_logger(db)
    logger.send(tag, v)

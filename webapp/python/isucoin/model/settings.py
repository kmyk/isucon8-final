from __future__ import annotations

import isubank
import isulogger


BANK_ENDPOINT = "bank_endpoint"
BANK_APPID = "bank_appid"
LOG_ENDPOINT = "log_endpoint"
LOG_APPID = "log_appid"

_isubank = None
_logger = None

def set_setting(db, k: str, v: str):
    global _isubank, _logger
    cur = db.cursor()
    cur.execute(
        "INSERT INTO setting (name, val) VALUES (%s, %s) ON DUPLICATE KEY UPDATE val = VALUES(val)",
        (k, v),
    )
    if k in ( BANK_ENDPOINT, BANK_APPID ):
        if _isubank is not None:
            _isubank = None
    if k in ( LOG_ENDPOINT, LOG_APPID ):
        if _logger is not None:
            _logger = None


def get_setting(db, k: str) -> str:
    cur = db.cursor()
    cur.execute("SELECT val FROM setting WHERE name = %s", (k,))
    return cur.fetchone()[0]


def get_isubank(db):
    global _isubank
    if _isubank is None:
        endpoint = get_setting(db, BANK_ENDPOINT)
        appid = get_setting(db, BANK_APPID)
        _isubank = isubank.IsuBank(endpoint, appid)
    return _isubank


def get_logger(db):
    global _logger
    if _logger is None:
        endpoint = get_setting(db, LOG_ENDPOINT)
        appid = get_setting(db, LOG_APPID)
        _logger = isulogger.IsuLogger(endpoint, appid)
    return _logger


def send_log(db, tag, v):
    logger = get_logger(db)
    logger.send(tag, v)

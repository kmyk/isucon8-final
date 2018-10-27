import contextlib
import datetime
import MySQLdb
import os

dbhost = os.environ.get("ISU_DB_HOST", "127.0.0.1")
dbport = os.environ.get("ISU_DB_PORT", "3306")
dbuser = os.environ.get("ISU_DB_USER", "root")
dbpass = os.environ.get("ISU_DB_PASSWORD", "")
dbname = os.environ.get("ISU_DB_NAME", "isucoin")

# ISUCON用初期データの基準時間です
# この時間以降のデータはinitializeで削除されます
base_time = datetime.datetime(2018, 10, 16, 10, 0, 0)

def get_new_dbconn():
    return MySQLdb.connect(
        host=dbhost,
        port=int(dbport),
        user=dbuser,
        password=dbpass,
        database=dbname,
        charset="utf8mb4",
        autocommit=True,
    )

_dbconn = None
def get_dbconn():
    # NOTE: get_dbconn() is not thread safe.  Don't use threaded server.
    global _dbconn
    if _dbconn is None:
        _dbconn = get_new_dbconn()
    return _dbconn

@contextlib.contextmanager
def transaction():
    conn = get_dbconn()
    conn.begin()
    try:
        yield conn
    except:
        conn.rollback()
        raise
    else:
        conn.commit()

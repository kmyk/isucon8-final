#!/bin/bash
set -e
ISU_DB_USER=isucon
ISU_DB_PASSWORD=isucon
ISU_DB_HOST=127.0.0.1
ISU_DB_PORT=3306
ISU_DB_NAME=isucoin

mysql -u$ISU_DB_USER -p$ISU_DB_PASSWORD --host $ISU_DB_HOST --port $ISU_DB_PORT <<EOF
DROP DATABASE ${ISU_DB_NAME};
CREATE DATABASE ${ISU_DB_NAME};
EOF
mysql -u$ISU_DB_USER -p$ISU_DB_PASSWORD --host $ISU_DB_HOST --port $ISU_DB_PORT $ISU_DB_NAME < isucoin.sql
mysql -u$ISU_DB_USER -p$ISU_DB_PASSWORD --host $ISU_DB_HOST --port $ISU_DB_PORT $ISU_DB_NAME < isucoin.dump.sql

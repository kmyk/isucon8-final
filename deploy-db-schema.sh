#!/bin/bash
set -e

for ip in $@ ; do
    for f in init-db.sh isucoin.sql; do
        scp $f isucon@$ip:~/
    done

ssh isucon@${ip} <<EOF
set -e
./init-db.sh
EOF

done

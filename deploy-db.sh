#!/bin/bash
set -e

for ip in $@ ; do
    for f in etc/my.cnf ; do
        scp $f isucon@$ip:~/
    done

ssh isucon@${ip} <<EOF
set -e
sudo mv my.cnf /etc/
sudo systemctl restart mysqld
EOF

done
echo OK

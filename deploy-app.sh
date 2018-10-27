#!/bin/bash
set -e
for ip in $@ ; do

    for f in webapp/python/* ; do
        scp -r $f isucon@$ip:~/isucon2018-final/webapp/python/
    done

    for f in env.sh etc/nginx/nginx.conf etc/systemd/system/isucoin.service ; do
        scp $f isucon@$ip:~/
    done

    ssh isucon@${ip} <<EOF
set -e
sudo mv nginx.conf /etc/nginx/
sudo mv isucoin.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart isucoin.service
sudo systemctl restart nginx.service
EOF

done
echo OK

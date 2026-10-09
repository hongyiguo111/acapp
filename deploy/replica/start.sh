#!/bin/bash
# Starts the services the way they run in production: redis and nginx as daemons, uwsgi and daphne typed into
# bash panes of a tmux session owned by the app user. Run inside the replica container once the app is in place.
set -e
redis-server --daemonize yes --bind 127.0.0.1 >/dev/null
nginx
/usr/sbin/sshd
su acs -c 'tmux kill-server 2>/dev/null || true'
su acs -c 'tmux new-session -d -s 0 -x 220 -y 60'
su acs -c 'tmux split-window -t 0'
su acs -c 'tmux split-window -t 0'
su acs -c "tmux send-keys -t 0:0.0 'cd /home/acs/acapp && uwsgi --ini uwsgi.ini' Enter"
su acs -c "tmux send-keys -t 0:0.1 'cd /home/acs/acapp && /usr/bin/python3 /usr/local/bin/daphne -b 0.0.0.0 -p 5015 acapp.asgi:application' Enter"
# pane 0.2 stays an idle shell, like the spare panes in production
for i in $(seq 1 30); do
    ss -ltn 2>/dev/null | grep -q ':8000' && ss -ltn | grep -q ':5015' && break
    sleep 1
done
ss -ltn | grep -E ':(80|443|8000|5015|6379) ' || true

#!/usr/bin/env python3
"""Close the nginx 'off-by-slash' hole in production. Run once; needs the root password (env SSH_PW).

    SSH_PW='...' python deploy/fix_nginx.py [--host H] [--port P]

The hole: `location /static {` together with `alias /home/acs/acapp/static/;` lets /static../<anything> escape into
/home/acs/acapp, i.e. /static../db.sqlite3, /static../.git/config, /static../acapp/settings.py are downloadable.

What this does inside the django_server container (nothing else):
  1. show the current lines and count the requests in the nginx access logs that used the hole (status + path only)
  2. back up /etc/nginx/nginx.conf, change `location /static {` to `location /static/ {` (exactly one line)
  3. nginx -t; only when it passes: nginx -s reload (graceful, no downtime); otherwise the backup is put back
  4. verify: normal static files still 200; the traversal URLs no longer serve the database / git files
"""
import argparse
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")

FIX = r'''
CONF=/etc/nginx/nginx.conf
echo "--- before:"; grep -nE 'location /static|alias /home/acs/acapp/static' $CONF
echo "--- access logs: requests that tried /static.. (count, status, path):"
( cat /var/log/nginx/access.log* 2>/dev/null; zcat /var/log/nginx/access.log*.gz 2>/dev/null ) | grep -F 'static..' | awk '{print $9, $7}' | sort | uniq -c | sort -rn | head -15
echo "(end of list; an empty list means no request used the hole in the logs that still exist)"
VULN='^[[:space:]]*location[[:space:]]+/static[[:space:]]*\{[[:space:]]*$'
SAFE='^[[:space:]]*location[[:space:]]+/static/[[:space:]]*\{[[:space:]]*$'
N=$(grep -cE "$VULN" $CONF)
if [ "$N" = "0" ] && grep -qE "$SAFE" $CONF; then echo "already fixed: location /static/ has its trailing slash"; exit 0; fi
if [ "$N" != "1" ]; then echo "expected exactly one line 'location /static {' but found $N - not changing anything"; exit 1; fi
BK=$CONF.bak-before-static-fix
[ -e "$BK" ] || cp -a $CONF $BK
sed -i -E 's#^([[:space:]]*)location[[:space:]]+/static[[:space:]]*\{#\1location /static/ {#' $CONF
echo "--- after:"; grep -nE 'location /static' $CONF
if nginx -t 2>&1; then
  nginx -s reload && echo "nginx reloaded"
else
  echo "nginx -t FAILED - restoring the backup, nothing reloaded"; cp -a $BK $CONF; nginx -t 2>&1; exit 1
fi
sleep 1
'''

CHECK = r'''
import http.client, ssl
ctx = ssl._create_unverified_context()
def status(path):
    c = http.client.HTTPSConnection("127.0.0.1", 443, context=ctx, timeout=15)
    c.request("GET", path, headers={"Host": "app7562.acapp.acwing.com.cn"})
    r = c.getresponse(); body = r.read(64); c.close()
    return r.status, body
ok = True
def check(label, cond, extra=""):
    global ok
    ok = ok and cond
    print(("PASS  " if cond else "FAIL  ") + label + "  " + extra)
for p in ("/static/js/dist/game.js", "/static/css/florr.css", "/"):
    s, b = status(p); check("still served: " + p, s == 200, str(s))
for p in ("/static../db.sqlite3", "/static../.git/config", "/static../.git/HEAD", "/static../acapp/settings.py"):
    s, b = status(p)
    check("hole closed: " + p, s != 200 and not b.startswith(b"SQLite") and not b.startswith(b"[core]"), str(s))
print("ALL OK" if ok else "SOME CHECKS FAILED")
raise SystemExit(0 if ok else 1)
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("ACAPP_DEPLOY_HOST", "39.96.169.44"))
    ap.add_argument("--port", type=int, default=22)
    ap.add_argument("--container", default="django_server")
    args = ap.parse_args()
    if not os.environ.get("SSH_PW"):
        sys.exit("set SSH_PW to the root password for this one command")
    import paramiko
    c = None
    for attempt in range(6):
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            c.connect(args.host, port=args.port, username="root", password=os.environ["SSH_PW"], timeout=20, banner_timeout=60,
                      auth_timeout=60, allow_agent=False, look_for_keys=False)
            break
        except Exception as ex:
            print("connect attempt %d failed: %s" % (attempt + 1, type(ex).__name__))
            time.sleep(4)
    else:
        sys.exit("cannot connect")

    def remote(cmd, stdin_text):
        ch = c.get_transport().open_session()
        ch.exec_command(cmd)
        ch.sendall(stdin_text.encode("utf-8"))
        ch.shutdown_write()
        out = b""
        while True:
            d = ch.recv(65536)
            if not d:
                break
            out += d
        return ch.recv_exit_status(), out.decode("utf-8", "replace")

    code, out = remote("docker exec -i %s bash -s" % args.container, FIX)
    print(out)
    if code != 0:
        sys.exit("fixing nginx failed (exit %d) - see above; the backup is /etc/nginx/nginx.conf.bak-before-static-fix" % code)
    code, out = remote("docker exec -i %s python3 -" % args.container, CHECK)
    print(out)
    c.close()
    print("To undo: cp -a /etc/nginx/nginx.conf.bak-before-static-fix /etc/nginx/nginx.conf && nginx -s reload  (inside the container)")
    return code


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""One-time setup of the deploy tooling on the production host. Needs the root password once (env SSH_PW), never stores it.

    SSH_PW='...' python deploy/install_server.py              install / update
    SSH_PW='...' python deploy/install_server.py --uninstall  remove everything this script added

What it changes on the HOST (not inside the container), and nothing else:
  1. /usr/local/bin/acapp-deploy        the server script (root:root, 0700) - replaced on every run
  2. /var/backups/acapp/                where deploys keep their database snapshot + replaced files (0700)
  3. /root/.ssh/authorized_keys         one line per deploy key, each restricted to
        command="/usr/local/bin/acapp-deploy",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty
     i.e. the key can ONLY run the deploy script (deploy / dry-run / status / rollback), never a shell.
     The previous file is copied to authorized_keys.bak-<time> first; existing keys (your own) are left alone.
It also creates (locally) the key pairs ~/.ssh/acapp_deploy (for you) and ~/.ssh/acapp_deploy_ci (for GitHub Actions) if
missing, and writes deploy/known_hosts from the host's own key files, read over the password-authenticated connection.
Finally it proves the setup: key login works, `status` runs, and an arbitrary command through the key is refused.
"""
import argparse
import os
import subprocess
import sys
import time
import warnings

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
HOST_DEFAULT = "39.96.169.44"
MARK = "acapp-deploy-"
FORCED = 'command="/usr/local/bin/acapp-deploy",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty'
SSH_DIR = os.path.join(os.path.expanduser("~"), ".ssh")


def say(msg=""):
    print(msg, flush=True)


def ensure_keypair(path, comment):
    if os.path.exists(path):
        say("  key exists: %s" % path)
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        r = subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", path])
        if r.returncode != 0:
            sys.exit("ssh-keygen failed")
        say("  created key: %s" % path)
    return open(path + ".pub", encoding="utf-8").read().strip()


def connect(host, port):
    import paramiko
    for attempt in range(1, 7):
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            c.connect(host, port=port, username="root", password=os.environ["SSH_PW"], timeout=20, banner_timeout=60,
                      auth_timeout=60, allow_agent=False, look_for_keys=False)
            return c
        except Exception as ex:
            say("  connect attempt %d failed: %s" % (attempt, type(ex).__name__))
            time.sleep(4)
    sys.exit("cannot connect to %s" % host)


def run(c, cmd, check=True):
    _, o, e = c.exec_command(cmd)
    out, err = o.read().decode("utf-8", "replace"), e.read().decode("utf-8", "replace")
    code = o.channel.recv_exit_status()
    if check and code != 0:
        sys.exit("remote command failed (%d): %s\n%s%s" % (code, cmd, out, err))
    return code, out, err


def put(c, local, remote, mode):
    # always upload with LF line endings: a CRLF checkout on Windows would turn the shebang into `python3\r` and break it
    data = open(local, "rb").read().replace(b"\r\n", b"\n")
    sftp = c.open_sftp()
    tmp = remote + ".new"
    with sftp.open(tmp, "wb") as f:
        f.write(data)
    sftp.chmod(tmp, mode)
    sftp.close()
    run(c, "chown root:root %s && mv -f %s %s" % (tmp, tmp, remote))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("ACAPP_DEPLOY_HOST", HOST_DEFAULT))
    ap.add_argument("--port", type=int, default=22)
    ap.add_argument("--key-dir", default=SSH_DIR, help="where the key pairs are created / read (default ~/.ssh)")
    ap.add_argument("--known-hosts", default=os.path.join(HERE, "known_hosts"), help="where the pinned host keys are written")
    ap.add_argument("--no-ci", action="store_true", help="do not create / install the GitHub Actions key")
    ap.add_argument("--uninstall", action="store_true")
    args = ap.parse_args()
    if not os.environ.get("SSH_PW"):
        sys.exit("set SSH_PW to the root password for this one command:  SSH_PW='...' python deploy/install_server.py")
    keys = {"local": os.path.join(args.key_dir, "acapp_deploy"), "ci": os.path.join(args.key_dir, "acapp_deploy_ci")}

    c = connect(args.host, args.port)
    if args.uninstall:
        say("removing the deploy keys and the script from the host")
        run(c, "cp -a /root/.ssh/authorized_keys /root/.ssh/authorized_keys.bak-uninstall-$(date +%%s) && "
               "grep -v '%s' /root/.ssh/authorized_keys > /root/.ssh/authorized_keys.tmp; mv -f /root/.ssh/authorized_keys.tmp /root/.ssh/authorized_keys; "
               "chmod 600 /root/.ssh/authorized_keys; rm -f /usr/local/bin/acapp-deploy" % MARK)
        say("done (backups in /var/backups/acapp were left in place)")
        return 0

    say("1/6 local deploy keys")
    pubs = {"local": ensure_keypair(keys["local"], MARK + "local")}
    if not args.no_ci:
        pubs["ci"] = ensure_keypair(keys["ci"], MARK + "ci")

    say("2/6 checking the host")
    _, out, _ = run(c, "python3 --version; docker ps --format '{{.Names}}' | grep -x django_server || echo 'NO django_server CONTAINER'")
    say("  " + out.strip().replace("\n", "\n  "))
    if "NO django_server" in out:
        sys.exit("the django_server container is not running - refusing to install")
    _, out, _ = run(c, "sshd -T 2>/dev/null | grep -Ei '^(permitrootlogin|pubkeyauthentication|authorizedkeysfile)' || true", check=False)
    say("  sshd: " + out.strip().replace("\n", " | "))
    if "pubkeyauthentication no" in out.lower() or "permitrootlogin no" in out.lower():
        sys.exit("sshd does not allow root key logins - change that deliberately first, nothing was installed")

    say("3/6 installing /usr/local/bin/acapp-deploy and /var/backups/acapp")
    put(c, os.path.join(HERE, "acapp_deploy_server.py"), "/usr/local/bin/acapp-deploy", 0o700)
    run(c, "python3 -m py_compile /usr/local/bin/acapp-deploy && rm -rf /usr/local/bin/__pycache__; mkdir -p /var/backups/acapp && chmod 700 /var/backups/acapp")
    say("  script installed and compiles with the host's python3")

    say("4/6 restricted keys in /root/.ssh/authorized_keys")
    run(c, "mkdir -p /root/.ssh && chmod 700 /root/.ssh && touch /root/.ssh/authorized_keys && "
           "cp -a /root/.ssh/authorized_keys /root/.ssh/authorized_keys.bak-$(date +%s)")
    _, current, _ = run(c, "cat /root/.ssh/authorized_keys")
    for name, pub in pubs.items():
        blob = pub.split()[1]
        if blob in current:
            say("  %s key already present (left as is)" % name)
            continue
        line = "%s %s" % (FORCED, pub)
        run(c, "printf '%%s\\n' '%s' >> /root/.ssh/authorized_keys" % line.replace("'", "'\\''"))
        say("  added the %s key (restricted to acapp-deploy)" % name)
    run(c, "chmod 600 /root/.ssh/authorized_keys")

    say("5/6 pinned host keys, read from the host's own key files")
    lines = []
    sftp = c.open_sftp()
    pattern = args.host if args.port == 22 else "[%s]:%d" % (args.host, args.port)
    for kind in ("ed25519", "ecdsa", "rsa"):
        try:
            with sftp.open("/etc/ssh/ssh_host_%s_key.pub" % kind) as f:
                parts = f.read().decode().split()
            lines.append("%s %s %s" % (pattern, parts[0], parts[1]))
        except IOError:
            pass
    sftp.close()
    if not lines:
        sys.exit("could not read any host key from /etc/ssh")
    with open(args.known_hosts, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    say("  wrote %d host key(s) to %s" % (len(lines), args.known_hosts))
    c.close()

    say("6/6 proof")
    base = ["ssh", "-i", keys["local"], "-p", str(args.port), "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
            "-o", "StrictHostKeyChecking=yes", "-o", "UserKnownHostsFile=" + args.known_hosts.replace("\\", "/"),
            "-o", "ConnectTimeout=20", "root@" + args.host]
    r = subprocess.run(base + ["status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8", "replace")
    say("  key login + `status`: exit %d\n    %s" % (r.returncode, "\n    ".join(out.strip().splitlines()[-8:])))
    ok1 = "acapp-deploy status" in out
    r2 = subprocess.run(base + ["id"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out2 = r2.stdout.decode("utf-8", "replace")
    ok2 = "uid=" not in out2 and r2.returncode == 3
    say("  the key must NOT run arbitrary commands (`id`): %s (exit %d: %s)" % ("refused, good" if ok2 else "NOT REFUSED - REMOVE THE KEYS", r2.returncode, out2.strip()[:80]))
    if not (ok1 and ok2):
        say("\nSETUP INCOMPLETE - see above. Nothing deploys until `status` works through the key.")
        return 1
    say("\nSetup complete. From now on:  python deploy/deploy.py")
    if not args.no_ci:
        say("GitHub Actions: add the content of %s as the repository secret DEPLOY_SSH_KEY (see deploy/README.md)." % keys["ci"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

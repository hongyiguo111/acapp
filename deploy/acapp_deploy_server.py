#!/usr/bin/env python3
"""acapp-deploy: server side of the one-command deploy. Runs on the HOST that runs the `django_server` container.

It is installed as /usr/local/bin/acapp-deploy and is the ONLY thing the deploy SSH keys may run (forced command in
authorized_keys). The release arrives as a tar stream on stdin; the mode is the first word of the ssh command:

    deploy     preflight, back up, apply, migrate, reload what changed, verify; roll back by itself if anything fails
    dry-run    the preflight only (copy of the live app + copy of the live database in a scratch dir: migrations, system
               check, full test suite) - the live site is not touched
    status     processes, recent deploys, backups, health checks
    rollback   put the files of the newest backup back and reload (the database is not touched)

Exit codes: 0 ok / nothing to do, 1 failed but the live site was restored, 2 failed and needs a human, 3 refused.
Python 3.8 compatible on purpose (that is what the host and the container run).
"""
import atexit
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time

CONTAINER = os.environ.get("ACAPP_CONTAINER", "django_server")
APP_DIR = "/home/acs/acapp"
APP_USER = "acs"
DOMAIN = "app7562.acapp.acwing.com.cn"
BACKUP_ROOT = os.environ.get("ACAPP_BACKUP_DIR", "/var/backups/acapp")
KEEP_BACKUPS = 10
STAGING = "/tmp/acapp_staging"
DAPHNE_CMD = "/usr/bin/python3 /usr/local/bin/daphne -b 0.0.0.0 -p 5015 acapp.asgi:application"
ALLOWED_TOP = ("acapp", "game", "match_system", "static")
ALLOWED_ROOT_FILES = ("manage.py",)
REQUIRED = ("manage.py", "acapp/settings.py", "game/routing.py")
MAX_RELEASE_BYTES = 200 * 1024 * 1024
NAME_RE = re.compile(r"^[A-Za-z0-9_./+@-]+$")
MODES = ("deploy", "dry-run", "status", "rollback")
LOCK_STALE_SECONDS = 30 * 60

_log_lines = []


def log(msg=""):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), msg)
    _log_lines.append(line)
    print(line, flush=True)


class Fail(Exception):
    """A step failed in a way that is already handled (message is for the human reading the log)."""


# ---- docker plumbing ----------------------------------------------------------------------------------------------
def docker_bin():
    return shutil.which("docker") or "docker"


def dx(args, user=None, stdin_path=None, stdin_bytes=None, timeout=600):
    """docker exec ... ; returns (returncode, stdout text, stderr text)."""
    cmd = [docker_bin(), "exec"]
    if stdin_path or stdin_bytes is not None:
        cmd.append("-i")
    if user:
        cmd += ["-u", user]
    cmd += [CONTAINER] + list(args)
    stdin = None
    if stdin_path:
        stdin = open(stdin_path, "rb")
    try:
        p = subprocess.run(cmd, stdin=stdin, input=stdin_bytes if stdin is None else None,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    finally:
        if stdin:
            stdin.close()
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def sh(script, user=None, timeout=600):
    return dx(["bash", "-s"], user=user, stdin_bytes=script.encode("utf-8"), timeout=timeout)


def py(script, user=None, timeout=600):
    return dx(["python3", "-"], user=user, stdin_bytes=script.encode("utf-8"), timeout=timeout)


def tail(text, n=25):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return "\n".join("      " + l for l in lines[-n:])


def run_step(title, script, user=None, timeout=600, show_ok=False):
    """Run a bash snippet in the container, fail loudly with the output tail."""
    code, out, err = sh(script, user=user, timeout=timeout)
    if code != 0:
        raise Fail("%s failed (exit %s)\n%s" % (title, code, tail(out + "\n" + err)))
    if show_ok:
        log(title + ": ok")
    return out


# ---- lock / backups -------------------------------------------------------------------------------------------------
def acquire_lock():
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    path = os.path.join(BACKUP_ROOT, ".lock")
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, ("%d %d" % (os.getpid(), time.time())).encode())
            os.close(fd)
            atexit.register(lambda: os.path.exists(path) and os.remove(path))
            return
        except FileExistsError:
            if time.time() - os.path.getmtime(path) > LOCK_STALE_SECONDS:
                log("removing a stale lock (older than %d min)" % (LOCK_STALE_SECONDS // 60))
                os.remove(path)
                continue
            raise Fail("another deploy is running (lock %s) - refusing" % path)
    raise Fail("could not take the deploy lock")


def backup_dirs():
    if not os.path.isdir(BACKUP_ROOT):
        return []
    return sorted(d for d in os.listdir(BACKUP_ROOT) if re.match(r"^\d{8}-\d{6}$", d))


def prune_backups():
    old = backup_dirs()[:-KEEP_BACKUPS]
    for d in old:
        shutil.rmtree(os.path.join(BACKUP_ROOT, d), ignore_errors=True)
    if old:
        log("pruned %d old backup(s), keeping the newest %d" % (len(old), KEEP_BACKUPS))


def write_deploy_log(outcome):
    try:
        os.makedirs(BACKUP_ROOT, exist_ok=True)
        with open(os.path.join(BACKUP_ROOT, "deploy.log"), "a", encoding="utf-8") as f:
            f.write("=== %s outcome=%s\n%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), outcome, "\n".join(_log_lines)))
    except OSError:
        pass


# ---- the release -----------------------------------------------------------------------------------------------------
def read_release(dest):
    total = 0
    with open(dest, "wb") as f:
        while True:
            block = sys.stdin.buffer.read(1 << 20)
            if not block:
                break
            total += len(block)
            if total > MAX_RELEASE_BYTES:
                raise Fail("release is larger than %d MB - refusing" % (MAX_RELEASE_BYTES // (1 << 20)), )
            f.write(block)
    if total == 0:
        raise Fail("no release on stdin")
    return total


def safe_name(name):
    """Return the normalised relative name of an allowed file, or None."""
    if not name or name.startswith("/") or "\\" in name or not NAME_RE.match(name):
        return None
    parts = name.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return None
    if len(parts) == 1:
        return name if name in ALLOWED_ROOT_FILES else None
    return name if parts[0] in ALLOWED_TOP else None


def inspect_release(path):
    """Validate every member and return {name: md5}. Only plain files in the allowed places pass."""
    files = {}
    with tarfile.open(path) as tf:
        for m in tf.getmembers():
            raw = m.name[2:] if m.name.startswith("./") else m.name
            if m.isdir():
                d = raw.rstrip("/")
                parts = d.split("/")
                if d and (parts[0] not in ALLOWED_TOP or any(p in ("", ".", "..") for p in parts) or not NAME_RE.match(d)):
                    raise Fail("directory outside the allowed places in the release: %r" % m.name)
                continue
            if not m.isreg():
                raise Fail("release contains something that is not a regular file: %r" % m.name)
            name = safe_name(raw)
            if name is None:
                raise Fail("release contains a file that is not allowed: %r" % m.name)
            files[name] = hashlib.md5(tf.extractfile(m).read()).hexdigest()
    missing = [r for r in REQUIRED if r not in files]
    if missing:
        raise Fail("release is incomplete, missing: %s" % ", ".join(missing))
    return files


def live_hashes(names):
    script = ("cd %s && while IFS= read -r f; do if [ -f \"$f\" ]; then md5sum -- \"$f\"; else echo \"MISSING  $f\"; fi; done\n" % APP_DIR)
    code, out, err = dx(["bash", "-c", script.rstrip("\n")], user=APP_USER, stdin_bytes=("\n".join(names) + "\n").encode(), timeout=300)
    if code != 0:
        raise Fail("could not read the live files (exit %s): %s" % (code, tail(err)))
    live = {}
    for line in out.splitlines():
        if line.startswith("MISSING  "):
            continue
        m = re.match(r"^([0-9a-f]{32})  (.+)$", line)
        if m:
            live[m.group(2)] = m.group(1)
    return live


def filtered_tar(src, names, dest):
    """A tar with only `names` (keeps content and mode), so unchanged files are not rewritten."""
    wanted = set(names)
    with tarfile.open(src) as tin, tarfile.open(dest, "w") as tout:
        for m in tin.getmembers():
            raw = m.name[2:] if m.name.startswith("./") else m.name
            if m.isreg() and raw in wanted:
                m.name = raw
                tout.addfile(m, tin.extractfile(m))


# ---- preflight in a scratch copy ---------------------------------------------------------------------------------------
SNAPSHOT_PY = """
import sqlite3, sys
src = sqlite3.connect('file:%(src)s?mode=ro', uri=True, timeout=30)
dst = sqlite3.connect('%(dst)s')
src.backup(dst)
dst.close(); src.close()
print('snapshot written')
"""


def snapshot_db(dst):
    code, out, err = py(SNAPSHOT_PY % {"src": APP_DIR + "/db.sqlite3", "dst": dst}, user=APP_USER, timeout=300)
    if code != 0:
        raise Fail("database snapshot failed: %s" % tail(out + err))


def preflight(filtered, tag):
    log("preflight: scratch copy of the live app + a copy of the live database (the live site is not touched)")
    try:
        run_step("copy the app", "set -e\nrm -rf %(s)s\ncp -a %(a)s %(s)s\nrm -f %(s)s/uwsgi.log\n" % {"s": STAGING, "a": APP_DIR}, user=APP_USER)
        code, out, err = dx(["tar", "-xf", "-", "-C", STAGING, "--no-same-owner"], user=APP_USER, stdin_path=filtered)
        if code != 0:
            raise Fail("could not unpack the release into the scratch copy: %s" % tail(err))
        snapshot_db(STAGING + "/db.sqlite3")
        env = "cd %s && export REDIS_PORT=1 PYTHONWARNINGS=ignore\n" % STAGING
        run_step("byte-compile", env + "python3 -m compileall -q acapp game match_system >/dev/null\n", user=APP_USER, show_ok=True)
        run_step("django check", env + "python3 manage.py check 2>&1\n", user=APP_USER, show_ok=True)
        run_step("model changes without a migration",
                 env + "python3 manage.py makemigrations --check --dry-run 2>&1\n", user=APP_USER, show_ok=True)
        out = run_step("migrations on the copy of the live database", env + "python3 manage.py migrate --noinput 2>&1\n", user=APP_USER)
        applied = [l.strip() for l in out.splitlines() if "Applying" in l]
        log("migrations on the copy: %s" % (("%d applied" % len(applied)) if applied else "nothing to apply"))
        out = run_step("test suite", env + "python3 manage.py test game --noinput 2>&1\n", user=APP_USER, timeout=900)
        summary = [l for l in out.splitlines() if l.startswith("Ran ") or l.strip() in ("OK",) or l.startswith("FAILED")]
        log("tests: %s" % " / ".join(s.strip() for s in summary))
    finally:
        sh("rm -rf %s\n" % STAGING, user=APP_USER)


# ---- backups ------------------------------------------------------------------------------------------------------------
def make_backup(existing_changed, meta):
    ts = time.strftime("%Y%m%d-%H%M%S")
    bdir = os.path.join(BACKUP_ROOT, ts)
    os.makedirs(bdir)
    tmp_in_container = "/tmp/acapp_snapshot_%s.sqlite3" % ts
    snapshot_db(tmp_in_container)
    try:
        p = subprocess.run([docker_bin(), "cp", "%s:%s" % (CONTAINER, tmp_in_container), os.path.join(bdir, "db.sqlite3")],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            raise Fail("docker cp of the database snapshot failed: %s" % p.stderr.decode("utf-8", "replace"))
    finally:
        dx(["rm", "-f", tmp_in_container])
    con = sqlite3.connect(os.path.join(bdir, "db.sqlite3"))
    try:
        result = con.execute("pragma integrity_check").fetchone()[0]
    finally:
        con.close()
    if result != "ok":
        raise Fail("the database snapshot failed its integrity check: %s" % result)
    cmd = [docker_bin(), "exec", "-i", "-u", APP_USER, CONTAINER, "tar", "-C", APP_DIR, "-cf", "-", "-T", "-"]
    p = subprocess.run(cmd, input=("\n".join(existing_changed) + "\n").encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise Fail("backup of the files that will be replaced failed: %s" % tail(p.stderr.decode("utf-8", "replace")))
    with open(os.path.join(bdir, "files.tar"), "wb") as f:
        f.write(p.stdout)
    meta = dict(meta, backup=ts)
    with open(os.path.join(bdir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    log("backup %s: database snapshot (integrity ok) + %d replaced file(s)" % (ts, len(existing_changed)))
    return bdir


# ---- reload what changed -------------------------------------------------------------------------------------------------
UWSGI_PIDS = r"""ps -eo pid,ppid,args | awk '/uwsgi --ini uwsgi.ini/ && !/awk/ {print $1, $2}'"""


def uwsgi_tree():
    code, out, err = sh(UWSGI_PIDS + "\n")
    rows = [tuple(map(int, l.split())) for l in out.splitlines() if l.strip()]
    pids = {p for p, _ in rows}
    masters = [p for p, pp in rows if pp not in pids]
    children = {p for p, pp in rows if pp in pids}
    return masters, children


def port_listening(port):
    code, out, err = sh("ss -ltn | grep -q ':%d ' && echo yes || echo no\n" % port)
    return out.strip() == "yes"


def reload_uwsgi():
    masters, before = uwsgi_tree()
    if len(masters) != 1:
        raise Fail("expected exactly one uwsgi master, found %s - not reloading it" % masters)
    master = masters[0]
    code, out, err = dx(["kill", "-HUP", str(master)])
    if code != 0:
        raise Fail("kill -HUP %d failed: %s" % (master, tail(err)))
    for _ in range(40):
        time.sleep(0.5)
        m2, after = uwsgi_tree()
        if m2 == [master] and after and not (after & before) and port_listening(8000):
            log("uwsgi reloaded gracefully (master %d kept, %d fresh workers)" % (master, len(after)))
            return
    raise Fail("uwsgi did not come back with fresh workers after SIGHUP")


PANE_OF = r"""
PID=%d
panes=$(tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{pane_pid}')
p=$PID
while [ -n "$p" ] && [ "$p" -gt 1 ]; do
  t=$(echo "$panes" | awk -v p="$p" '$2==p {print $1}')
  if [ -n "$t" ]; then echo "$t"; exit 0; fi
  p=$(ps -o ppid= -p "$p" | tr -d ' ')
done
exit 1
"""


def daphne_pids():
    code, out, err = sh("pgrep -f '/usr/local/bin/daphne -b 0.0.0.0 -p 5015' || true\n")
    return [int(x) for x in out.split()]


def pane_of_daphne(pid):
    code, out, err = sh(PANE_OF % pid, user=APP_USER)
    target = out.strip()
    if code != 0 or not target:
        raise Fail("could not find the tmux pane daphne runs in (pid %d)" % pid)
    return target


# The tmux pane daphne lives in, remembered BEFORE anything is restarted: if the new daphne crashes on start there is no
# process left to find the pane from, and the rollback still has to start the old one in the same pane.
KNOWN = {"daphne_pane": None}


def restart_daphne():
    pids = daphne_pids()
    if len(pids) > 1:
        raise Fail("expected one daphne process, found %s - not touching it" % pids)
    target = KNOWN["daphne_pane"] or (pane_of_daphne(pids[0]) if pids else None)
    if not target:
        log("daphne is not running and its tmux pane is unknown - leaving the websocket server alone")
        return
    if pids:
        dx(["tmux", "send-keys", "-t", target, "C-c"], user=APP_USER)
        for _ in range(40):
            time.sleep(0.5)
            if not daphne_pids():
                break
        else:
            raise Fail("daphne did not stop after Ctrl-C in pane %s - NOT starting a second one" % target)
    dx(["tmux", "send-keys", "-t", target, "cd %s && %s" % (APP_DIR, DAPHNE_CMD), "Enter"], user=APP_USER)
    for _ in range(60):
        time.sleep(0.5)
        if daphne_pids() and port_listening(5015):
            log("daphne restarted in tmux pane %s (websocket players reconnect)" % target)
            return
    raise Fail("daphne did not come back on port 5015")


# ---- verification -----------------------------------------------------------------------------------------------------------
CHECK_PY = r'''
import http.client, json, socket, ssl, sys
DOMAIN = "%(domain)s"
ctx = ssl._create_unverified_context()
def get(path):
    c = http.client.HTTPSConnection("127.0.0.1", 443, context=ctx, timeout=15)
    c.request("GET", path, headers={"Host": DOMAIN})
    r = c.getresponse(); body = r.read(); c.close()
    return r.status, body
failed = []
def check(label, ok, extra=""):
    print(("PASS  " if ok else "FAIL  ") + label + ("  " + extra if extra else ""))
    if not ok:
        failed.append(label)
s, b = get("/"); check("home page", s == 200, str(s))
s, b = get("/settings/getinfo/?platform=WEB"); check("getinfo api", s == 200 and b"result" in b, str(s))
s, b = get("/settings/ranklist/"); check("duel ranking api", s == 200, str(s))
s, b = get("/settings/florr_ranklist/")
try:
    ok = s == 200 and json.loads(b)["result"] == "success"
except Exception:
    ok = False
check("florr ranking api", ok, str(s))
s, b = get("/static/js/dist/game.js"); check("game.js served, no hardcoded production origin", s == 200 and b"app7562" not in b, "%%s, %%d bytes" %% (s, len(b)))
s, b = get("/static/css/florr.css"); check("florr.css served", s == 200, str(s))
try:
    sk = socket.create_connection(("127.0.0.1", 5015), timeout=10)
    sk.sendall(("GET /wss/florr/ HTTP/1.1\r\nHost: 127.0.0.1:5015\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\nOrigin: https://" + DOMAIN + "\r\n\r\n").encode())
    line = sk.recv(200).decode(errors="replace").split("\r\n")[0]; sk.close()
    check("florr websocket route (anonymous must get 403)", " 403" in line, line)
except Exception as ex:
    check("florr websocket route reachable on 5015", False, repr(ex))
# informational only: the nginx off-by-slash hole must never fail a deploy, but it must not stay unnoticed
s, b = get("/static../db.sqlite3")
if s == 200 and b.startswith(b"SQLite format 3"):
    print("WARN  nginx 'location /static' hole is still open: /static../db.sqlite3 serves the live database")
print("ALL OK" if not failed else "FAILED: " + ", ".join(failed))
sys.exit(1 if failed else 0)
'''


def run_checks():
    """Returns ({label: passed}, raw output, warnings)."""
    code, out, err = py(CHECK_PY % {"domain": DOMAIN}, timeout=120)
    results, warns = {}, []
    for line in (out or "").splitlines():
        if line.startswith("PASS  ") or line.startswith("FAIL  "):
            results[line[6:].split("  ")[0].strip()] = line.startswith("PASS")
        elif line.startswith("WARN"):
            warns.append(line)
    return results, out + err, warns


def verify(attempts=4, must_pass=None):
    """True when the site is healthy. `must_pass` = labels that have to pass (used after a rollback to the OLD version,
    which legitimately lacks the checks of the new one); None = every check has to pass."""
    last_out = ""
    for _ in range(attempts):
        results, last_out, warns = run_checks()
        need = list(results) if must_pass is None else list(must_pass)
        failing = [label for label in need if not results.get(label, False)]
        if results and not failing:
            for w in warns:
                log(w)
            log("verification: %s" % ("all checks passed" if must_pass is None else "everything that worked before still works"))
            return True
        time.sleep(3)
    log("verification FAILED:\n" + tail(last_out, 20))
    return False


# ---- modes ----------------------------------------------------------------------------------------------------------------
def restore_files(bdir):
    files_tar = os.path.join(bdir, "files.tar")
    code, out, err = dx(["tar", "-xf", "-", "-C", APP_DIR, "--no-same-owner"], user=APP_USER, stdin_path=files_tar)
    if code != 0:
        raise Fail("restoring the files from %s failed: %s" % (files_tar, tail(err)))


def reload_all(reloaded):
    if reloaded:
        reload_uwsgi()
        restart_daphne()


def rollback_after_failure(bdir, reloaded, migrated, baseline):
    log("ROLLING BACK: putting the previous files back")
    try:
        restore_files(bdir)
        reload_all(reloaded)
        ok = verify(must_pass=[label for label, passed in baseline.items() if passed])
    except Fail as e:
        log("rollback problem: %s" % e)
        return False
    if migrated:
        log("note: database migrations of this release stay applied (they are additive); the pre-deploy snapshot is %s/db.sqlite3" % bdir)
    return ok


def do_deploy(dry_run):
    release = os.path.join(tempfile.mkdtemp(prefix="acapp-release-"), "release.tar")
    atexit.register(lambda: shutil.rmtree(os.path.dirname(release), ignore_errors=True))
    size = read_release(release)
    names = inspect_release(release)
    log("release received: %d files, %.1f MB, sha256 %s" % (len(names), size / 1048576.0, hashlib.sha256(open(release, "rb").read()).hexdigest()[:16]))

    live = live_hashes(sorted(names))
    changed = sorted(n for n, h in names.items() if live.get(n) != h)
    if not changed:
        log("nothing to deploy: every file in the release is identical to the live one")
        return 0
    added = [n for n in changed if n not in live]
    existing_changed = [n for n in changed if n in live]
    py_changed = any(n.endswith(".py") and n != "game/tests.py" for n in changed)
    log("%d file(s) differ (%d new, %d replaced); python code changed: %s" % (len(changed), len(added), len(existing_changed), "yes" if py_changed else "no"))
    if dry_run:
        log("(dry-run) first changed files: " + ", ".join(changed[:6]) + (" ..." if len(changed) > 6 else ""))
    filtered = release + ".changed"
    filtered_tar(release, changed, filtered)

    preflight(filtered, "x")
    if dry_run:
        log("DRY RUN OK - nothing on the live site was changed")
        return 0

    # never deploy on top of a site that is already broken: the rollback could not tell the difference
    baseline, _, _ = run_checks()
    if not baseline.get("home page") or not baseline.get("getinfo api"):
        raise Fail("the live site is not healthy before the deploy (home page / getinfo api do not answer) - fix that first, nothing was changed")
    pids = daphne_pids()
    if not pids:
        raise Fail("daphne (the websocket server) is not running - start it in its tmux pane first, nothing was changed")
    KNOWN["daphne_pane"] = pane_of_daphne(pids[0])
    log("health before the deploy: %d of %d checks pass%s; daphne runs in tmux pane %s" % (sum(baseline.values()), len(baseline),
        "" if all(baseline.values()) else " (the old version lacks some of the new features)", KNOWN["daphne_pane"]))
    bdir = make_backup(existing_changed, {"changed": changed, "python_changed": py_changed})
    reloaded = migrated = False
    try:
        code, out, err = dx(["tar", "-xf", "-", "-C", APP_DIR, "--no-same-owner"], user=APP_USER, stdin_path=filtered)
        if code != 0:
            raise Fail("unpacking the release into %s failed: %s" % (APP_DIR, tail(err)))
        log("files applied")
        if py_changed:
            out = run_step("migrate", "cd %s && python3 manage.py migrate --noinput 2>&1\n" % APP_DIR, user=APP_USER)
            applied = [l.strip() for l in out.splitlines() if "Applying" in l]
            migrated = bool(applied)
            log("live migrations: %s" % (", ".join(a.replace("Applying ", "").replace("... OK", "").strip() for a in applied) or "nothing to apply"))
            reload_uwsgi()
            reloaded = True
            restart_daphne()
        else:
            log("only templates / static files changed: no reload needed")
        if not verify():
            raise Fail("post-deploy verification failed")
    except Fail as e:
        log("DEPLOY FAILED: %s" % e)
        if rollback_after_failure(bdir, reloaded, migrated, baseline):
            log("the previous version is serving again (rolled back)")
            return 1
        log("ROLLBACK DID NOT VERIFY - needs a human. Backup: %s" % bdir)
        return 2
    prune_backups()
    log("DEPLOY OK (backup %s)" % os.path.basename(bdir))
    return 0


def do_rollback():
    dirs = backup_dirs()
    if not dirs:
        raise Fail("no backup to roll back to")
    bdir = os.path.join(BACKUP_ROOT, dirs[-1])
    meta = json.load(open(os.path.join(bdir, "meta.json"), encoding="utf-8"))
    log("rolling back to the files saved before deploy %s (%d changed file(s))" % (dirs[-1], len(meta.get("changed", []))))
    restore_files(bdir)
    reload_all(meta.get("python_changed", True))
    ok = verify(must_pass=[])   # the old version may lack newer checks; we only insist that the site answers (home page)
    ok = ok and bool(run_checks()[0].get("home page"))
    log("note: the database is untouched; its pre-deploy snapshot is %s/db.sqlite3" % bdir)
    return 0 if ok else 2


def do_status():
    masters, children = uwsgi_tree()
    log("uwsgi master %s, %d workers; daphne pids %s" % (masters, len(children), daphne_pids()))
    for d in backup_dirs()[-5:]:
        try:
            meta = json.load(open(os.path.join(BACKUP_ROOT, d, "meta.json"), encoding="utf-8"))
            log("backup %s: %d files, python changed: %s" % (d, len(meta.get("changed", [])), meta.get("python_changed")))
        except Exception:
            log("backup %s" % d)
    return 0 if verify(attempts=1) else 1


def parse_mode(argv):
    words = os.environ.get("SSH_ORIGINAL_COMMAND", "").split() or argv[1:]
    mode = words[0] if words else ""
    if mode not in MODES or len(words) > 1:
        print("usage: acapp-deploy {%s}" % "|".join(MODES), file=sys.stderr)
        sys.exit(3)
    return mode


def main(argv):
    mode = parse_mode(argv)
    outcome = "error"
    code = 2
    try:
        acquire_lock()
        log("acapp-deploy %s (container %s)" % (mode, CONTAINER))
        if mode in ("deploy", "dry-run"):
            code = do_deploy(dry_run=(mode == "dry-run"))
        elif mode == "rollback":
            code = do_rollback()
        else:
            code = do_status()
        outcome = {0: "ok", 1: "rolled-back", 2: "needs-attention"}.get(code, "error")
    except Fail as e:
        log("REFUSED/FAILED: %s" % e)
        code, outcome = 3, "refused"
    except subprocess.TimeoutExpired as e:
        log("TIMEOUT: %s" % e)
        code, outcome = 2, "timeout"
    except Exception as e:  # never leave the caller with a bare traceback and no log
        log("UNEXPECTED ERROR: %r" % (e,))
        code, outcome = 2, "error"
    if mode in ("deploy", "rollback"):
        write_deploy_log(outcome)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))

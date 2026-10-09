"""End-to-end scenarios for the deploy tooling against the local replica (deploy/replica/setup_replica.py).

    python deploy/tests/replica_scenarios.py [--keep]

Each scenario builds a throw-away commit in a temporary git worktree (never pushed, branches deleted at the end), deploys it to
the replica with `deploy.py --local`, and asserts both the exit code and the state of the replica afterwards.
Needs Docker Desktop and the replica container (default name acapp_replica) at a state where HEAD is deployed:
the script first deploys HEAD itself, so it can be re-run at any time.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONTAINER = os.environ.get("ACAPP_CONTAINER", "acapp_replica")
BACKUPS = os.path.join(tempfile.gettempdir(), "acapp_replica_backups")
ENV = dict(os.environ, ACAPP_CONTAINER=CONTAINER, ACAPP_BACKUP_DIR=BACKUPS, PYTHONIOENCODING="utf-8")
DOCKER = shutil.which("docker") or os.path.expandvars(r"%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin\docker.exe")
BRANCHES = []
results = []


def check(label, cond, extra=""):
    results.append(bool(cond))
    print(("  PASS  " if cond else "  FAIL  ") + label + (("   [" + extra + "]") if extra and not cond else ""))


def dexec(*args, user=None):
    cmd = [DOCKER, "exec"] + (["-u", user] if user else []) + [CONTAINER] + list(args)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def http_status(path):
    code, out = dexec("python3", "-c",
        "import http.client, ssl\n"
        "c = http.client.HTTPSConnection('127.0.0.1', 443, context=ssl._create_unverified_context(), timeout=15)\n"
        "c.request('GET', %r, headers={'Host': 'app7562.acapp.acwing.com.cn'})\n"
        "print(c.getresponse().status)" % path)
    return int(out.strip() or 0)


def md5_live(path):
    return dexec("md5sum", "/home/acs/acapp/" + path)[1].split()[0]


def procs():
    code, out = dexec("bash", "-c", "ps -eo pid,ppid,args | awk '/uwsgi --ini/ && !/awk/ {print $1\":\"$2}' | sort | tr '\\n' ' '; "
                      "pgrep -f '/usr/local/bin/[d]aphne -b 0.0.0.0 -p 5015' | tr '\\n' ' '")
    return out.strip()


def deploy(ref=None, *extra):
    cmd = [sys.executable, os.path.join(ROOT, "deploy", "deploy.py"), "--local"] + (["--ref", ref] if ref else []) + list(extra)
    p = subprocess.run(cmd, env=ENV, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True).stdout.decode("utf-8", "replace")


def make_branch(name, mutate):
    """Commit `mutate(worktree_dir)` on top of HEAD as branch `name` without touching the main checkout."""
    wt = tempfile.mkdtemp(prefix="acapp-wt-")
    shutil.rmtree(wt)
    git("worktree", "add", "-q", "-b", name, wt, "HEAD")
    try:
        mutate(wt)
        git("add", "-A", cwd=wt)
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", name, cwd=wt)
    finally:
        git("worktree", "remove", "--force", wt)
    BRANCHES.append(name)
    return name


def append(path, text):
    def f(wt):
        with open(os.path.join(wt, path), "a", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    return f


def replace_in(path, old, new):
    def f(wt):
        full = os.path.join(wt, path)
        s = open(full, encoding="utf-8", newline="").read()
        assert old in s, (path, old)
        open(full, "w", encoding="utf-8", newline="").write(s.replace(old, new, 1))
    return f


def new_file(path, text):
    def f(wt):
        full = os.path.join(wt, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w", encoding="utf-8", newline="\n").write(text)
    return f


def backups_count():
    return len([d for d in os.listdir(BACKUPS) if d[:1].isdigit()]) if os.path.isdir(BACKUPS) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="keep the temporary branches")
    ap.parse_args()

    print("== baseline: deploy HEAD (idempotent)")
    code, out = deploy()
    check("HEAD deploys (or is already live)", code == 0, out[-400:])
    check("site healthy", http_status("/") == 200 and http_status("/settings/florr_ranklist/") == 200)

    print("== 1. deploying the same release again does nothing")
    n = backups_count(); before = procs()
    code, out = deploy()
    check("exit 0 and 'nothing to deploy'", code == 0 and "nothing to deploy" in out, out[-300:])
    check("no new backup, no process touched", backups_count() == n and procs() == before)

    print("== 2. static-only change: no reload")
    before = procs()
    b = make_branch("tmp-deploy-static", append("static/css/florr.css", "\n/* deploy test */\n"))
    code, out = deploy(b)
    check("exit 0", code == 0, out[-400:])
    check("says no reload is needed", "no reload needed" in out, out[-400:])
    check("uwsgi workers and daphne untouched", procs() == before, "%s -> %s" % (before, procs()))
    check("file is live", "deploy test" in dexec("cat", "/home/acs/acapp/static/css/florr.css")[1])

    print("== 3. a failing test is stopped in the preflight")
    n = backups_count(); h = md5_live("game/tests.py")
    b = make_branch("tmp-deploy-failing-test", append("game/tests.py", "\n\nclass Boom(unittest.TestCase):\n    def test_boom(self):\n        self.fail('deliberate')\n"))
    code, out = deploy(b)
    check("exit 3 and the test suite is named", code == 3 and "test suite" in out and "FAILED" in out, out[-500:])
    check("live file untouched, no backup made, scratch dir removed",
          md5_live("game/tests.py") == h and backups_count() == n and dexec("ls", "/tmp")[1].find("acapp_staging") < 0)

    print("== 4. a migration that crashes is stopped in the preflight")
    boom = ("from django.db import migrations\n\n\ndef explode(apps, schema_editor):\n    raise RuntimeError('deliberate migration failure')\n\n\n"
            "class Migration(migrations.Migration):\n    dependencies = [('game', '0011_florr_petal_rarity')]\n    operations = [migrations.RunPython(explode)]\n")
    b = make_branch("tmp-deploy-bad-migration", new_file("game/migrations/0012_boom.py", boom))
    n = backups_count()
    code, out = deploy(b)
    check("exit 3, the migration step is named", code == 3 and "migrations on the copy of the live database failed" in out, out[-500:])
    check("live site untouched", backups_count() == n and http_status("/settings/getinfo/?platform=WEB") == 200)

    print("== 5. a model change without a migration is stopped")
    b = make_branch("tmp-deploy-no-migration", replace_in("game/models/florr/florr.py", "kills_total = models.PositiveIntegerField(default=0)",
                                                          "kills_total = models.PositiveIntegerField(default=0)\n    nickname = models.CharField(max_length=20, default='')"))
    code, out = deploy(b)
    check("exit 3 and 'without a migration'", code == 3 and "without a migration" in out, out[-500:])

    print("== 6. a bug the tests cannot see: verification fails -> automatic rollback")
    good = md5_live("game/views/settings/getinfo.py")
    b = make_branch("tmp-deploy-soft-break", replace_in("game/views/settings/getinfo.py", "def getinfo(request):", "def getinfo(request):\n    raise RuntimeError('deliberate')\n\n\ndef _unused(request):"))
    code, out = deploy(b)
    check("exit 1 (failed, rolled back)", code == 1, out[-700:])
    check("rollback is announced", "ROLLING BACK" in out and "rolled back" in out, out[-700:])
    check("the previous file and a working site are back", md5_live("game/views/settings/getinfo.py") == good and http_status("/settings/getinfo/?platform=WEB") == 200)

    print("== 7. a release that only crashes under uwsgi: the reload fails -> automatic rollback")
    good = md5_live("acapp/wsgi.py"); before = procs()
    b = make_branch("tmp-deploy-uwsgi-break", append("acapp/wsgi.py", "\nimport sys\nif 'uwsgi' in sys.modules:\n    raise RuntimeError('deliberate: only fails under uwsgi')\n"))
    code, out = deploy(b)
    check("exit 1 (failed, rolled back)", code == 1, out[-900:])
    check("the old wsgi.py is back and the site answers", md5_live("acapp/wsgi.py") == good and http_status("/") == 200 and http_status("/settings/getinfo/?platform=WEB") == 200)

    print("== 8. a release whose daphne cannot start: the restart fails -> automatic rollback")
    good = md5_live("acapp/asgi.py")
    b = make_branch("tmp-deploy-daphne-break", append("acapp/asgi.py", "\nraise RuntimeError('deliberate: daphne cannot import this')\n"))
    code, out = deploy(b)
    check("exit 1 (failed, rolled back)", code == 1, out[-900:])
    code2, o2 = dexec("bash", "-c", "ss -ltn | grep -c ':5015 '")
    check("asgi.py restored and daphne is listening again", md5_live("acapp/asgi.py") == good and o2.strip() == "1", o2)

    print("== 9. manual rollback restores the previous release")
    b = make_branch("tmp-deploy-marker", replace_in("game/views/settings/getinfo.py", "def getinfo(request):", "def getinfo(request):\n    # marker-9"))
    code, out = deploy(b)
    check("marker deployed", code == 0 and "marker-9" in dexec("cat", "/home/acs/acapp/game/views/settings/getinfo.py")[1], out[-500:])
    code, out = deploy(None, "rollback")
    check("rollback exits 0", code == 0, out[-500:])
    check("marker is gone, site healthy", "marker-9" not in dexec("cat", "/home/acs/acapp/game/views/settings/getinfo.py")[1] and http_status("/settings/getinfo/?platform=WEB") == 200)

    print("== 10. status works")
    code, out = deploy(None, "status")
    check("status exits 0 and lists backups", code == 0 and "backup" in out, out[-400:])

    print("== cleanup: back to HEAD")
    code, out = deploy()
    check("HEAD deployed again", code == 0, out[-400:])
    if not ap.parse_args().keep:
        for b in BRANCHES:
            subprocess.run(["git", "branch", "-D", b], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = all(results)
    print("\n%d/%d checks passed" % (sum(results), len(results)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

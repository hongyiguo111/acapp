#!/usr/bin/env python3
"""One-command deploy of a git commit to the production server (details and one-time setup: deploy/README.md).

    python deploy/deploy.py                 deploy HEAD
    python deploy/deploy.py --dry-run       preflight only: migrations on a copy of the live database + all tests; changes nothing
    python deploy/deploy.py status          processes, recent deploys, health checks
    python deploy/deploy.py rollback        put back the files saved before the last deploy
    python deploy/deploy.py --ref v1.2      deploy another commit / tag / branch

The release is `git archive` of the runtime directories, so only committed files are deployed. It is streamed over
SSH to /usr/local/bin/acapp-deploy, which the deploy key is restricted to. Exit code = the server script's:
0 ok, 1 failed but the previous version was restored, 2 failed and needs a human, 3 refused / preflight failed.

`--local` runs the server script on this machine instead of over SSH (used by the replica tests; needs ACAPP_CONTAINER).
"""
import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RELEASE_PATHS = ["acapp", "game", "match_system", "static", "manage.py"]
DEFAULT_HOST = "39.96.169.44"
MODES = ("deploy", "dry-run", "status", "rollback")


def git(*args, **kw):
    return subprocess.run(["git", *args], cwd=ROOT, **kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", nargs="?", default="deploy", choices=("deploy", "status", "rollback"))
    ap.add_argument("--dry-run", action="store_true", help="preflight only, change nothing")
    ap.add_argument("--ref", default="HEAD", help="commit / tag / branch to deploy (default HEAD)")
    ap.add_argument("--host", default=os.environ.get("ACAPP_DEPLOY_HOST", DEFAULT_HOST))
    ap.add_argument("--port", default="22")
    ap.add_argument("--user", default="root")
    ap.add_argument("--key", default=os.environ.get("ACAPP_DEPLOY_KEY", os.path.join(os.path.expanduser("~"), ".ssh", "acapp_deploy")))
    ap.add_argument("--known-hosts", default=os.path.join(HERE, "known_hosts"))
    ap.add_argument("--local", action="store_true", help="run the server script locally instead of over ssh (tests)")
    args = ap.parse_args()
    mode = "dry-run" if args.dry_run else args.mode
    if args.dry_run and args.mode != "deploy":
        ap.error("--dry-run only goes with deploy")

    release = None
    if mode in ("deploy", "dry-run"):
        p = git("rev-parse", "--verify", "--quiet", args.ref + "^{commit}", stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if p.returncode != 0:
            sys.exit("unknown git ref: %s" % args.ref)
        sha = p.stdout.decode().strip()
        desc = git("log", "-1", "--format=%h %s", sha, stdout=subprocess.PIPE).stdout.decode("utf-8", "replace").strip()
        dirty = git("status", "--porcelain", "--", *RELEASE_PATHS, stdout=subprocess.PIPE).stdout.decode().strip()
        print("deploying commit: %s" % desc)
        if dirty:
            print("note: uncommitted changes in the runtime directories are NOT part of the release:\n  " + "\n  ".join(dirty.splitlines()[:8]))
        tmp = tempfile.mkdtemp(prefix="acapp-release-")
        release = os.path.join(tmp, "release.tar")
        r = git("archive", "--format=tar", "-o", release, sha, "--", *RELEASE_PATHS)
        if r.returncode != 0:
            sys.exit("git archive failed")
        print("release: %.1f MB" % (os.path.getsize(release) / 1048576.0))

    if args.local:
        cmd = [sys.executable, os.path.join(HERE, "acapp_deploy_server.py"), mode]
    else:
        if not os.path.isfile(args.key):
            sys.exit("deploy key not found: %s\nrun deploy/install_server.py once first (see deploy/README.md)" % args.key)
        if not os.path.isfile(args.known_hosts):
            sys.exit("missing %s - it is created by deploy/install_server.py" % args.known_hosts)
        cmd = ["ssh", "-i", args.key, "-p", str(args.port),
               "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "UserKnownHostsFile=" + args.known_hosts.replace("\\", "/"),
               "-o", "ConnectTimeout=20", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=8",
               "%s@%s" % (args.user, args.host), mode]

    stdin = open(release, "rb") if release else subprocess.DEVNULL
    try:
        code = subprocess.run(cmd, stdin=stdin).returncode
    finally:
        if release:
            stdin.close()
            try:
                os.remove(release)
                os.rmdir(os.path.dirname(release))
            except OSError:
                pass
    messages = {
        0: "done",
        1: "FAILED - the previous version was restored, the site is serving as before",
        2: "FAILED and the rollback did not verify - the site needs a human (see the log above)",
        3: "refused or the preflight failed - nothing on the live site was changed",
        255: "ssh could not connect or the key was refused (is the deploy key installed? see deploy/README.md)",
    }
    print("\n%s (exit %d)" % (messages.get(code, "unexpected exit code"), code))
    return code


if __name__ == "__main__":
    sys.exit(main())

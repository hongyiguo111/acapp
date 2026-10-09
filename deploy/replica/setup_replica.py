"""Build and start the local production stand-in.

    python deploy/replica/setup_replica.py [--name acapp_replica] [--base 117e803]

The app inside starts at an OLD commit (default 117e803 = the tree that ran in production before the florr mode)
with a throw-away database made of synthetic users, so a deploy of HEAD exercises real migrations. No production
data is used. Needs Docker Desktop running.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))


def docker(*args, check=True, **kw):
    docker_bin = shutil.which("docker") or os.path.expandvars(r"%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin\docker.exe")
    return subprocess.run([docker_bin, *args], check=check, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="acapp_replica")
    ap.add_argument("--base", default="117e803", help="git commit the replica starts from")
    ap.add_argument("--image", default="acapp-replica:latest")
    args = ap.parse_args()

    print("building image (first time takes a few minutes)...")
    docker("build", "-t", args.image, HERE)

    docker("rm", "-f", args.name, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    docker("run", "-d", "--name", args.name, "-p", "127.0.0.1:2222:22", args.image, stdout=subprocess.DEVNULL)

    # the old application tree
    with tempfile.TemporaryDirectory() as tmp:
        tar = os.path.join(tmp, "base.tar")
        subprocess.run(["git", "archive", "--format=tar", "-o", tar, args.base, "--", "acapp", "game", "match_system", "static",
                        "manage.py", "uwsgi.ini", "scripts/uwsgi.ini"], cwd=ROOT, check=True)
        docker("exec", args.name, "mkdir", "-p", "/home/acs/acapp")
        with open(tar, "rb") as f:
            docker("exec", "-i", args.name, "tar", "-xf", "-", "-C", "/home/acs/acapp", stdin=f)
    docker("exec", args.name, "chown", "-R", "acs:acs", "/home/acs")

    # database with synthetic users, migrated to what that old tree knows
    docker("exec", "-u", "acs", args.name, "bash", "-c",
           "cd /home/acs/acapp && python3 manage.py migrate --noinput 2>&1 | tail -3 && "
           "python3 manage.py shell -c \"from django.contrib.auth.models import User; "
           "from game.models.player.player import Player; "
           "[Player.objects.get_or_create(user=User.objects.create_user('u%d' % i, password='x')) for i in range(5)]; "
           "print('users', User.objects.count())\"")
    docker("exec", args.name, "/usr/local/bin/start-services.sh")
    print("\nreplica '%s' is up (app at commit %s)." % (args.name, args.base))


if __name__ == "__main__":
    sys.exit(main())

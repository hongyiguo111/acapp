"""Security tests for what the server script accepts. No Docker needed:  python -m unittest deploy.tests.test_release_validation"""
import io
import os
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import acapp_deploy_server as srv  # noqa: E402


def make_tar(members, extra=None):
    """members: {name: bytes}; extra: callable(tarfile) for odd member types."""
    fd, path = tempfile.mkstemp(suffix=".tar")
    os.close(fd)
    with tarfile.open(path, "w") as tf:
        for name, data in members.items():
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
        if extra:
            extra(tf)
    return path


GOOD = {"manage.py": b"x", "acapp/settings.py": b"s", "game/routing.py": b"r", "game/static/css/a.css": b"c",
        "static/js/dist/game.js": b"j", "match_system/src/main.py": b"m"}


class InspectRelease(unittest.TestCase):
    def reject(self, members, extra=None, fragment=""):
        path = make_tar(members, extra)
        try:
            with self.assertRaises(srv.Fail) as cm:
                srv.inspect_release(path)
            self.assertIn(fragment, str(cm.exception))
        finally:
            os.remove(path)

    def test_a_normal_release_passes_and_is_hashed(self):
        path = make_tar(GOOD)
        try:
            files = srv.inspect_release(path)
        finally:
            os.remove(path)
        self.assertEqual(set(files), set(GOOD))
        self.assertEqual(len(files["manage.py"]), 32)

    def test_path_traversal_is_refused(self):
        for bad in ("../evil.py", "game/../../evil.py", "game/../manage.py/../../x", "acapp/../../../etc/cron.d/x"):
            self.reject(dict(GOOD, **{bad: b"x"}), fragment="not allowed")

    def test_absolute_paths_are_refused(self):
        self.reject(dict(GOOD, **{"/etc/passwd": b"x"}), fragment="not allowed")

    def test_places_outside_the_allowed_directories_are_refused(self):
        for bad in ("db.sqlite3", "uwsgi.log", ".git/config", "scripts/evil.sh", "deploy/x.py", "docs/x.md", "evil.py", "gamex/y.py"):
            self.reject(dict(GOOD, **{bad: b"x"}), fragment="not allowed")

    def test_suspicious_file_names_are_refused(self):
        for bad in ("game/a b.py", "game/a;b.py", "game/$(id).py", "game/`id`.py", "game/a\nb.py", "game/a|b", "game/a'b", 'game/a"b',
                    "game/中文.png", "game/a\\b.py", "game//b.py", "game/./b.py"):
            self.reject(dict(GOOD, **{bad: b"x"}), fragment="not allowed")

    def test_links_and_devices_are_refused(self):
        def symlink(tf):
            ti = tarfile.TarInfo("game/link")
            ti.type = tarfile.SYMTYPE
            ti.linkname = "/etc/passwd"
            tf.addfile(ti)

        def hardlink(tf):
            ti = tarfile.TarInfo("game/hard")
            ti.type = tarfile.LNKTYPE
            ti.linkname = "manage.py"
            tf.addfile(ti)

        def device(tf):
            ti = tarfile.TarInfo("game/dev")
            ti.type = tarfile.CHRTYPE
            tf.addfile(ti)
        for extra in (symlink, hardlink, device):
            self.reject(GOOD, extra, fragment="not a regular file")

    def test_directories_must_be_inside_the_allowed_tree(self):
        def good_dir(tf):
            ti = tarfile.TarInfo("game/consumers/")
            ti.type = tarfile.DIRTYPE
            tf.addfile(ti)

        def bad_dir(tf):
            ti = tarfile.TarInfo("etc/")
            ti.type = tarfile.DIRTYPE
            tf.addfile(ti)

        def dotdot_dir(tf):
            ti = tarfile.TarInfo("game/../")
            ti.type = tarfile.DIRTYPE
            tf.addfile(ti)
        path = make_tar(GOOD, good_dir)
        try:
            srv.inspect_release(path)
        finally:
            os.remove(path)
        self.reject(GOOD, bad_dir, fragment="directory outside")
        self.reject(GOOD, dotdot_dir, fragment="directory outside")

    def test_an_incomplete_release_is_refused(self):
        for missing in ("manage.py", "acapp/settings.py", "game/routing.py"):
            members = {k: v for k, v in GOOD.items() if k != missing}
            self.reject(members, fragment="incomplete")

    def test_empty_or_garbage_input_is_refused(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"this is not a tar file")
        os.close(fd)
        try:
            with self.assertRaises(Exception):
                srv.inspect_release(path)
        finally:
            os.remove(path)


class Modes(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("SSH_ORIGINAL_COMMAND", None)

    def tearDown(self):
        os.environ.pop("SSH_ORIGINAL_COMMAND", None)
        if self._saved is not None:
            os.environ["SSH_ORIGINAL_COMMAND"] = self._saved

    def test_allowed_modes_from_ssh(self):
        for mode in srv.MODES:
            os.environ["SSH_ORIGINAL_COMMAND"] = mode
            self.assertEqual(srv.parse_mode(["prog"]), mode)

    def test_everything_else_is_refused(self):
        for cmd in ("", "deploy; rm -rf /", "deploy extra", "bash", "/bin/sh -c id", "DEPLOY", "deploy&&id", "$(id)", "rollback --force", "scp -t /"):
            os.environ["SSH_ORIGINAL_COMMAND"] = cmd
            with self.assertRaises(SystemExit) as cm:
                srv.parse_mode(["prog"])
            self.assertEqual(cm.exception.code, 3, cmd)

    def test_mode_from_argv_when_not_forced(self):
        self.assertEqual(srv.parse_mode(["prog", "status"]), "status")
        with self.assertRaises(SystemExit):
            srv.parse_mode(["prog", "status", "extra"])


class Lock(unittest.TestCase):
    def test_a_second_deploy_is_refused_and_a_stale_lock_is_replaced(self):
        old = srv.BACKUP_ROOT
        srv.BACKUP_ROOT = tempfile.mkdtemp()
        try:
            lock = os.path.join(srv.BACKUP_ROOT, ".lock")
            open(lock, "w").write("1 1")
            with self.assertRaises(srv.Fail):
                srv.acquire_lock()
            stale = os.path.getmtime(lock) - srv.LOCK_STALE_SECONDS - 60
            os.utime(lock, (stale, stale))
            srv.acquire_lock()                     # replaces the stale lock
            self.assertTrue(os.path.exists(lock))
            with self.assertRaises(srv.Fail):      # and now it is held again
                srv.acquire_lock()
        finally:
            lock = os.path.join(srv.BACKUP_ROOT, ".lock")
            if os.path.exists(lock):
                os.remove(lock)
            srv.BACKUP_ROOT = old


class FilteredTar(unittest.TestCase):
    def test_only_the_requested_files_are_kept_with_their_content(self):
        src = make_tar(GOOD)
        dest = src + ".out"
        try:
            srv.filtered_tar(src, ["manage.py", "game/routing.py"], dest)
            with tarfile.open(dest) as tf:
                names = sorted(m.name for m in tf.getmembers())
                self.assertEqual(names, ["game/routing.py", "manage.py"])
                self.assertEqual(tf.extractfile("manage.py").read(), b"x")
        finally:
            os.remove(src)
            if os.path.exists(dest):
                os.remove(dest)


if __name__ == "__main__":
    unittest.main()

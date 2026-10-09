"""Bundle game/static/js/src/**/*.js into game/static/js/dist/game.js (local equivalent of compress_game_js.sh).

Files are concatenated in sorted path order and minified with terser as an ES module.
Needs Node (npx downloads terser on first use). Afterwards run `manage.py collectstatic` to sync static/.

    python scripts/build_js.py            # writes game/static/js/dist/game.js
    python scripts/build_js.py SRC OUT    # custom paths
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def build(src, out):
    files = sorted(src.rglob("*.js"), key=lambda p: p.relative_to(src).as_posix().encode())
    if not files:
        raise SystemExit(f"no .js files under {src}")
    tmp = out.with_name(out.name + ".cat.js")
    tmp.write_bytes(b"".join(f.read_bytes() for f in files))
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise SystemExit("npx not found - install Node.js")
    try:
        r = subprocess.run([npx, "--yes", "terser", str(tmp), "-c", "-m", "--module", "-o", str(out)],
                           capture_output=True, text=True)
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        raise SystemExit(f"terser failed:\n{r.stderr[-2000:]}")
    print(f"bundled {len(files)} files -> {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        build(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
    else:
        build(ROOT / "game/static/js/src", ROOT / "game/static/js/dist/game.js")

"""Runs grimoire's tools on this vault repo, fetching them on first use (a cloud session has no plugin).

  python3 .grimoire/run.py grim ARGS...      python3 .grimoire/run.py inscribe ARGS...
  python3 .grimoire/run.py hook start|prompt (used by .claude/settings.json; puts grim and inscribe on PATH)

Written by `grim scaffold`. The tools live in a cache folder outside this repo (GRIMOIRE_TOOLS moves it).
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

TOOLS_URL = "{TOOLS_URL}"
ROOT = Path(__file__).resolve().parent.parent
if os.name == "nt":
    _cache = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
else:
    _cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
TOOLS = Path(os.environ.get("GRIMOIRE_TOOLS") or _cache / "grimoire-tools")


def fetch():
    """Clone the tools once, update them at most hourly; offline, keep whatever copy there is."""
    stamp = TOOLS / ".git" / "grimoire-fetched"
    if not (TOOLS / ".git").is_dir():
        TOOLS.parent.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        clone = ["clone", "-q", "--depth", "1", TOOLS_URL, str(TOOLS)]
        if subprocess.run(["git", *clone], capture_output=True, env=env).returncode and shutil.which("gh"):
            subprocess.run(["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
                            *clone], capture_output=True, env=env)  # git has no login: use the GitHub CLI's
    elif not stamp.exists() or time.time() - stamp.stat().st_mtime > 3600:
        subprocess.run(["git", "-C", str(TOOLS), "pull", "-q", "--ff-only"], capture_output=True)
    if (TOOLS / ".git").is_dir():
        stamp.touch()
    return (TOOLS / "lib" / "grim.py").is_file()


def main(args):
    hook = args[:1] == ["hook"]
    if not fetch():
        if hook:
            return 0  # no tools (offline on first use): stay quiet rather than break the session
        print(f"grimoire: couldn't fetch the tools from {TOOLS_URL}", file=sys.stderr)
        return 1
    if args[:2] == ["hook", "start"] and os.environ.get("CLAUDE_ENV_FILE"):
        bin_ = TOOLS / "bin"
        with open(os.environ["CLAUDE_ENV_FILE"], "a") as f:  # grim / inscribe as plain commands this session
            f.write(f'export PATH="{bin_.as_posix()}:$PATH"\nexport GRIMOIRE_CHECKOUT="{ROOT.as_posix()}"\n')
    tool, rest = ("grim", args) if hook or not args or args[0] not in ("grim", "inscribe") else (args[0], args[1:])
    env = {**os.environ, "GRIMOIRE_CHECKOUT": str(ROOT)}
    return subprocess.run([sys.executable, "-X", "utf8", str(TOOLS / "lib" / f"{tool}.py"), *rest], env=env).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

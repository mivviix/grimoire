"""Self-check of grim + inscribe against throwaway vaults. Run: python3 tests/test_grimoire.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
TMP = tempfile.TemporaryDirectory()
BASE = {k: v for k, v in os.environ.items() if not k.startswith(("GRIMOIRE_", "GIT_"))} | {"XDG_CACHE_HOME": f"{TMP.name}/cache",
                                                                                         "CLAUDE_CONFIG_DIR": f"{TMP.name}/claude",
                                                                                         "XDG_DATA_HOME": f"{TMP.name}/data"}


def run(tool, *args, stdin=None, ok=True, env=None, code=None, cwd=None):
    script = [str(LIB / f"{tool}.py")] if tool in ("grim", "inscribe") else [tool]
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", *script, *args], input=stdin or "", cwd=cwd,
                       capture_output=True, text=True, env=env or {**BASE, "GRIMOIRE_VAULT": vault})
    want = code if code is not None else (0 if ok else None)
    assert (r.returncode == want) if want is not None else r.returncode != 0, \
        f"{tool} {args}: rc={r.returncode}\n{r.stdout}{r.stderr}"
    return r.stdout + r.stderr


CALLS = iter(range(10**6))


def hook(kind, prompt="", sid=None, env=None):
    sid = sid or ("s1" if kind == "prompt" else f"start{next(CALLS)}")  # each start is a new session unless given
    return run("grim", "hook", kind, stdin=json.dumps({"prompt": prompt, "session_id": sid}), env=env)


# --- a local vault from nothing ---------------------------------------------------
vault = f"{TMP.name}/v1/vault"
assert "empty" in run("grim")
run("inscribe", "jot", "first find")
run("inscribe", "new", "engine/ownership", "-s", "who simulates physics", "-t", "physics,Net", "--new-shelf", "engine",
    stdin="# Ownership\n\n## Rules\n- one\n\n## Other\ntext [[Spring.luau]]\n")
run("inscribe", "new", "snippets/Spring.luau", "-s", "a spring", "--new-shelf", "code", stdin="return {}\n")
run("inscribe", "new", "magic/x", "-s", "nope", stdin="x", ok=False)           # unknown shelf needs --new-shelf
run("inscribe", "new", "engine/y", "-s", "s", "--new-shelf", "again", stdin="x", ok=False)
run("inscribe", "new", "engine/ownership", "-s", "dup", stdin="x", ok=False)    # no overwrite
run("inscribe", "new", "engine/Bad_Name", "-s", "x", stdin="x", ok=False)

run("inscribe", "add", "ownership", "-s", "rules", stdin="- two\n")
text = Path(f"{vault}/engine/ownership.md").read_text()
assert "- one\n- two\n\n## Other" in text, text                                # list stays a list
run("inscribe", "replace", "ownership", "text", "prose")
run("inscribe", "replace", "ownership", "zzz", "y", ok=False)
run("inscribe", "meta", "Spring", "-s", "a damped spring")
assert Path(f"{vault}/snippets/Spring.luau").read_text().count("summary:") == 1

assert run("grim", "find", "simulates").startswith("engine/ownership — who simulates physics")
out = run("grim", "show", "ownership", "-s", "other")
assert "prose" in out and "- one" not in out and "Spring.luau — a damped spring" in out, out
assert "engine       1" in run("grim") and "inbox" in run("grim")
assert "net" in run("grim", "show", "ownership")                               # tags lowercased

# skills, folder entries, tools
run("inscribe", "new", "engine/slash-vfx", "-s", "how to make a sword slash effect", stdin="# Slash\n\nsteps\n")
src = Path(f"{TMP.name}/src")
(src / "data").mkdir(parents=True)
(src / "main.py").write_text("import os, sys\nprint('cache', os.environ['GRIMOIRE_CACHE'], *sys.argv[1:])\n")
(src / "data" / "palette.txt").write_text("red\n")
(src / "__pycache__").mkdir()
(src / "__pycache__" / "junk.pyc").write_text("x")
run("inscribe", "put", "tools/echo", str(src), ok=False)                       # new folder needs -s
run("inscribe", "put", "tools/echo", str(src), "-s", "prints its args", "--new-shelf", "runnable tools")
assert not Path(f"{vault}/tools/echo/__pycache__").exists()
out = run("grim", "show", "echo")
assert "data/palette.txt" in out and "grim run tools/echo" in out, out
assert "cache" in run("grim", "run", "echo", "hi") and "hi" in run("grim", "run", "echo", "hi")
big = Path(f"{TMP.name}/big.bin")
big.write_bytes(b"0" * (5 * 1024 * 1024 + 1))
assert "5 MB" in run("inscribe", "put", "tools/echo", str(big), ok=False)
assert not Path(f"{vault}/tools/echo/big.bin").exists()
run("grim", "run", "ownership", ok=False)                                     # not a tool

# skills: SKILL.md folders, listed at session start, read whole, never linked anywhere
ref = Path(f"{TMP.name}/ref.md")
ref.write_text("long reference\n")
run("inscribe", "skill", "engine/rig-check", stdin="steps\n", ok=False)              # new skill needs -d
run("inscribe", "skill", "engine/rig-check", "-d", "x\ny", stdin="steps\n", ok=False)  # one line
run("inscribe", "skill", "engine/rig-check", str(ref), "-d", "Check an R15 rig before animating it",
    stdin="# Rig check\n\n" + "\n".join(f"- step {i}" for i in range(80)) + "\n")
skill_md = Path(f"{vault}/engine/rig-check/SKILL.md").read_text()
assert skill_md.startswith("---\nname: rig-check\ndescription: Check an R15 rig before animating it\n---\n"), skill_md
assert "rig-check — Check an R15 rig" in run("grim", "skills")
out = run("grim", "show", "rig-check")
assert "- step 79" in out and "ref.md" in out, out                             # whole, plus its files
run("inscribe", "skill", "engine/rig-check", "-d", "Check a rig (R15 or R6) before animating it")  # update
assert "step 79" in run("grim", "show", "rig-check")                           # body kept
run("inscribe", "meta", "rig-check", "-t", "x", ok=False)                      # skills have no tags
run("inscribe", "put", "engine/rig-check", str(ref), "-s", "x", ok=False)      # not a folder entry
start = hook("start", sid="sk")
assert "rig-check — Check a rig (R15 or R6)" in start, start
assert "rig-check" not in hook("prompt", "check the rig before animating", sid="sk")  # listed already
assert not Path(f"{TMP.name}/claude").exists()

# hooks: prompt matching, seen-set, start primer, private notes
out = hook("prompt", "I'm making a slash effect for the sword")
assert "engine/slash-vfx" in out, out
assert "engine/slash-vfx" not in hook("prompt", "another slash effect for the sword")  # shown once per session
assert "engine/slash-vfx" in hook("prompt", "slash effect sword", sid="s2")
assert hook("prompt", "hello there") == ""
run("inscribe", "me", "likes short answers")
assert "likes short answers" in hook("start")
assert not any("likes short" in p.read_text(errors="ignore") for p in Path(vault).rglob("*") if p.is_file())
run("grim", "config", "me", "off")
assert "likes short answers" not in hook("start")
run("inscribe", "me", "x", ok=False)
Path(f"{vault}/engine/broken.md").write_text("---\nsummary: s\n---\n# B\n[[nowhere]]\n")
assert "broken link [[nowhere]]" in run("inscribe", "check", ok=False)

# --- two people share one vault through a bare "GitHub" repo -----------------------
tmp = f"{TMP.name}/sync"
os.makedirs(tmp)
sh = lambda *c, cwd=tmp, env=None: subprocess.run(c, cwd=cwd, check=True, capture_output=True, env=env)
person = lambda who: {**BASE, "GRIMOIRE_HOME": f"{tmp}/{who}", "GIT_AUTHOR_NAME": who,
                      "GIT_AUTHOR_EMAIL": f"{who}@x", "GIT_COMMITTER_NAME": who, "GIT_COMMITTER_EMAIL": f"{who}@x"}
a, b = person("a"), person("b")
sh("git", "init", "-q", "--bare", "-b", "main", "up.git")
sh("git", "clone", "-q", "up.git", "seed")
Path(f"{tmp}/seed/README.md").write_text("repo without a vault folder yet\n")
sh("git", "add", "-A", cwd=f"{tmp}/seed", env=a)
sh("git", "commit", "-qm", "seed", cwd=f"{tmp}/seed", env=a)
sh("git", "push", "-q", "origin", "HEAD:main", cwd=f"{tmp}/seed", env=a)

assert "isn't set up" in run("grim", env=a, ok=False)
assert "no vault on this machine" in hook("start", env=a)
run("grim", "init", f"{tmp}/up.git", env=a)
run("grim", "init", f"{tmp}/up.git", env=b)
hook("start", env=b)                                                         # b's last-seen point
run("inscribe", "new", "engine/streaming", "-s", "streaming facts", "--new-shelf", "engine", stdin="- x\n", env=a)
log = subprocess.run(["git", "--git-dir", f"{tmp}/up.git", "log", "--oneline"], capture_output=True, text=True)
assert "inscribe: new engine/streaming.md" in log.stdout, log.stdout          # pushed upstream
os.utime(f"{tmp}/b/.git/grimoire-pulled", (0, 0))                            # reads pull at most once a minute
assert "streaming facts" in run("grim", "find", "streaming", env=b)          # the other machine sees it
assert "engine/streaming — streaming facts" in hook("start", env=b)          # ...and is told it's new
run("inscribe", "add", "streaming", stdin="- from b\n", env=b)
run("inscribe", "add", "streaming", stdin="- from a\n", env=a)              # a must pull b's edit first
assert "from b" in run("grim", "show", "streaming", env=a)
os.utime(f"{tmp}/b/.git/grimoire-pulled", (0, 0))                            # expire b's read cache
out = run("grim", "show", "streaming", env=b)
assert "from a" in out and "from b" in out, out
hook("start", env=a)
run("inscribe", "add", "streaming", stdin="- a again\n", env=a)
assert "New or changed" not in hook("start", env=a)                          # own edits aren't news

run("inscribe", "skill", "engine/net-debug", "-d", "Debug network ownership glitches", stdin="steps\n", env=a)
os.utime(f"{tmp}/b/.git/grimoire-pulled", (0, 0))
assert "net-debug — Debug network ownership" in hook("start", env=b)          # the other agent sees the skill

# trust: b must read a's tool before running it, and again after a changes it
run("inscribe", "put", "tools/echo", str(src / "main.py"), "-s", "echo", "--new-shelf", "tools", env=a)
assert "a" in run("grim", "run", "echo", env=a)                              # own tool: no check
os.utime(f"{tmp}/b/.git/grimoire-pulled", (0, 0))
assert "changed by someone else" in run("grim", "run", "echo", env=b, code=2)
assert "cache" in run("grim", "run", "--ok", "echo", env=b)
assert "cache" in run("grim", "run", "echo", env=b)                          # trusted now
(src / "main.py").write_text("print('changed')\n")
run("inscribe", "put", "tools/echo", str(src / "main.py"), env=a)
os.utime(f"{tmp}/b/.git/grimoire-pulled", (0, 0))
out = run("grim", "run", "echo", env=b, code=2)
assert "+print('changed')" in out, out                                       # shows the diff
assert "changed" in run("grim", "run", "echo", "--ok", env=b)

# private notes never reach git
run("inscribe", "me", "secret preference", env=a)
everything = subprocess.run(["git", "--git-dir", f"{tmp}/up.git", "log", "-p", "--all"], capture_output=True, text=True)
assert "secret preference" not in everything.stdout

# --- the vault repo opened directly: a folder on a PC, a cloud session on a side branch --------
sh("git", "init", "-q", "--bare", "-b", "main", "veul.git")
sh("git", "clone", "-q", "veul.git", "pc")
pc, phone, tools = f"{tmp}/pc", f"{tmp}/phone", Path(f"{tmp}/tools")
(tools / ".git").mkdir(parents=True)                                         # stands in for the fetched tools
for d in ("lib", "commands", "skills", "bin"):
    try:
        (tools / d).symlink_to(LIB.parent / d)
    except OSError:                                                          # Windows without symlink rights
        __import__("shutil").copytree(LIB.parent / d, tools / d)
a_pc = {k: v for k, v in a.items() if k != "GRIMOIRE_HOME"} | {"GRIMOIRE_TOOLS": str(tools)}
assert "added:" in run("grim", "scaffold", "--tools", "https://example.invalid/grimoire", env=a_pc, cwd=pc)
assert Path(f"{pc}/.grimoire-vault").exists() and "example.invalid" in Path(f"{pc}/.grimoire/run.py").read_text()
assert "nothing to add" in run("grim", "scaffold", "--tools", "https://example.invalid/grimoire", env=a_pc, cwd=pc)
os.makedirs(f"{pc}/vault", exist_ok=True)
run("inscribe", "new", "ui/buttons", "-s", "button facts", "--new-shelf", "ui", stdin="- x\n", env=a_pc, cwd=f"{pc}/vault")
main_log = lambda: subprocess.run(["git", "--git-dir", f"{tmp}/veul.git", "log", "--oneline", "main"],
                                  capture_output=True, text=True).stdout
assert "new ui/buttons.md" in main_log()                                     # pushed from the PC folder
sh("git", "clone", "-q", "veul.git", "phone")
sh("git", "checkout", "-qb", "claude/some-session", cwd=phone)
b_phone = {k: v for k, v in b.items() if k != "GRIMOIRE_HOME"} | {"GRIMOIRE_TOOLS": str(tools),
                                                                   "CLAUDE_ENV_FILE": f"{tmp}/envfile"}
start = run(f"{phone}/.grimoire/run.py", "hook", "start", stdin='{"session_id": "ph"}', env=b_phone, cwd=phone)
assert "vault repo itself" in start and "ui (1)" in start, start
assert "GRIMOIRE_CHECKOUT" in Path(f"{tmp}/envfile").read_text()
assert run(f"{phone}/.grimoire/run.py", "hook", "start", stdin='{"session_id": "ph"}', env=b_phone, cwd=phone) == ""
run(f"{phone}/.grimoire/run.py", "inscribe", "add", "buttons", stdin="- from the phone\n", env=b_phone, cwd=phone)
assert "add to ui/buttons" in main_log()                                     # side branch saves land on main
os.utime(f"{pc}/.git/grimoire-pulled", (0, 0))
assert "from the phone" in run("grim", "show", "buttons", env=a_pc, cwd=pc)
assert not subprocess.run(["git", "-C", pc, "status", "--porcelain"], capture_output=True, text=True).stdout  # state stays in .git

print("ok")

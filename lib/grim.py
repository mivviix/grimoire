"""grim: read the grimoire, the shared vault agents build for themselves, without flooding the context window.

  grim                          the shelves and what each holds
  grim ls [SHELF]               entries with their one-line summaries
  grim find WORDS...            best matches (name, tags, summary, body) with the line that matched
  grim show NAME [-s HEADING]   an entry; a long one prints its outline, -s one section, --full all of it
  grim path NAME                absolute path of an entry (a file, or a tool/asset folder)
  grim run NAME [ARGS...]       run a tool entry (its main.py; uv for one that declares dependencies)
      [--ok]                    ...after reading changes others made to it since you last ran it
  grim me                       your private notes (on this machine only, never pushed)
  grim init URL                 first-time setup: clone the shared vault from its git URL
  grim config [me on|off]       show or change settings
  grim hook start|prompt        used by the plugin's hooks (reads hook JSON on stdin)

NAME is shelf/name as `ls` prints it; a bare name works when it is unique. Write with `inscribe`.

The vault lives upstream (its git remote). grim reads a private clone that it pulls first, at most once a
minute; inscribe pulls before and pushes after every write. GRIMOIRE_HOME moves the clone, GRIMOIRE_VAULT
uses a plain local folder with no syncing (tests, offline work).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _data_home():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def _cache_home():
    if os.name == "nt":
        return _data_home() / "grimoire-cache"
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "grimoire"


LOCAL = os.environ.get("GRIMOIRE_VAULT")  # set: a plain folder, never synced
CLONE = Path(os.environ.get("GRIMOIRE_HOME") or _data_home() / "grimoire")
VAULT = Path(LOCAL).resolve() if LOCAL else CLONE / "vault"
_BASE = VAULT if LOCAL else CLONE
STATE = _BASE.with_name(_BASE.name + "-state")  # config, last session, tools run, hook seen-sets
ME = _BASE.with_name(_BASE.name + "-me") / "notes.md"  # private; outside the clone so it can never be pushed
FRESH = 60  # seconds a read trusts the last pull
SHOW_MAX = 120  # lines; a longer entry prints its outline unless --full or -s
MAX_FILE = 5 * 1024 * 1024  # bigger files stay local: tools make or download them
CODE = {".luau": "--", ".lua": "--", ".py": "#"}  # code entries carry `-- summary:` / `-- tags:` header lines
FOLDER = "ENTRY.md"  # a folder entry (tool, asset set) describes itself here
LINK = re.compile(r"\[\[([^\[\]|#\n]+)(?:[|#][^\]\n]*)?\]\]")  # single-line only: Luau's --[[ ]] isn't a link
HEAD = re.compile(r"^(#{1,6})\s+(.*)")
META = re.compile(r"^\s*(?:--|#)\s*(summary|tags|use-when):\s*(.*)")
START_BUDGET, PROMPT_BUDGET = 2500, 1500  # chars the hooks may add to the context


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def warn(msg):
    print(f"grimoire: {msg}", file=sys.stderr)


# --- state and settings (local, never pushed) ---------------------------------

def load(name, default):
    try:
        return json.loads((STATE / name).read_text())
    except (OSError, ValueError):
        return default


def save(name, data):
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / name).write_text(json.dumps(data, indent=1))


def setting(key, default):
    return load("config.json", {}).get(key, default)


# --- sync with the upstream vault ---------------------------------------------

def git(*args, cwd=None):
    return subprocess.run(["git", "-C", str(cwd or CLONE), *args], capture_output=True, text=True)


def ready():
    return bool(LOCAL) or (CLONE / ".git").is_dir()


def _pull():
    if git("rev-parse", "--abbrev-ref", "@{u}").returncode == 0:
        return git("pull", "-q", "--rebase")
    branch = git("branch", "--show-current").stdout.strip() or "main"
    r = git("pull", "-q", "--rebase", "origin", branch)
    if r.returncode == 0:
        git("branch", "-q", "-u", f"origin/{branch}")
    elif "couldn't find remote ref" in r.stderr:  # a brand-new, still empty vault
        r.returncode = 0
    return r


def sync(force=False):
    """Pull the upstream vault into the clone and push commits still waiting. Reads pull at most every FRESH s."""
    if LOCAL:
        return
    if not ready():
        die("grimoire isn't set up on this machine: ask the user for the vault's git URL, then `grim init URL`")
    stamp = CLONE / ".git" / "grimoire-pulled"
    if not force and stamp.exists() and time.time() - stamp.stat().st_mtime < FRESH:
        return
    r = _pull()
    if r.returncode:
        git("rebase", "--abort")
        warn(f"couldn't pull, using the last copy ({r.stderr.strip()[:200]})")
    else:
        stamp.touch()
    push()


def push():
    """Push local commits; on a race, rebase onto upstream and retry once. Unpushed commits wait for next time."""
    if LOCAL or git("rev-parse", "-q", "--verify", "HEAD").returncode:
        return
    if git("rev-parse", "--abbrev-ref", "@{u}").returncode == 0 and git("rev-list", "--count", "@{u}..HEAD").stdout.strip() == "0":
        return
    if git("push", "-q", "-u", "origin", "HEAD").returncode == 0:
        return
    if _pull().returncode == 0 and git("push", "-q", "-u", "origin", "HEAD").returncode == 0:
        return
    git("rebase", "--abort")
    warn("saved locally but not pushed yet (offline or no push access); it goes up on the next run")


def me_email():
    ident = git("var", "GIT_AUTHOR_IDENT", cwd=CLONE if ready() and not LOCAL else VAULT.parent).stdout
    m = re.search(r"<([^>]*)>", ident)
    return m[1] if m else ""


# --- reading entries ----------------------------------------------------------

def shelves():
    if not VAULT.is_dir():  # an empty vault has no folder until its first shelf
        return []
    return sorted(p for p in VAULT.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def about(shelf):
    f = shelf / "_about.md"
    return next((l.strip() for l in f.read_text().splitlines() if l.strip()), "") if f.exists() else ""


def parse(path, folder=None):
    """-> dict(name, shelf, path, dir, summary, tags, use, body). Body excludes frontmatter / header lines."""
    text = path.read_text(errors="replace")
    meta, body = {}, text
    if path.suffix == ".md":
        if text.startswith("---\n") and "\n---" in text[4:]:
            head, body = text[4:].split("\n---", 1)
            body = body.lstrip("-").lstrip("\n")
            for line in head.splitlines():
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
    else:
        keep = []
        for i, line in enumerate(text.splitlines(keepends=True)):
            m = META.match(line) if i < 10 else None
            if m:
                meta[m[1]] = m[2].strip()
            else:
                keep.append(line)
        body = "".join(keep)
    rel = (folder or path).relative_to(VAULT)
    return {
        "name": (rel if folder or path.suffix != ".md" else rel.with_suffix("")).as_posix(),  # "/" on Windows too
        "shelf": rel.parts[0],
        "path": path,
        "dir": folder,
        "summary": meta.get("summary", ""),
        "tags": [t.strip() for t in meta.get("tags", "").strip("[]").split(",") if t.strip()],
        "use": meta.get("use-when", ""),
        "body": body,
    }


def entries(shelf=None):
    out = []
    for s in shelves():
        if shelf and s.name != shelf:
            continue
        for p in sorted(s.iterdir()):
            if p.name.startswith((".", "_")):
                continue
            if p.is_dir() and (p / FOLDER).is_file():
                out.append(parse(p / FOLDER, p))
            elif p.is_file() and (p.suffix == ".md" or p.suffix in CODE):
                out.append(parse(p))
    return out


def resolve(q, all_=None):
    all_ = all_ if all_ is not None else entries()
    q = q.strip().rstrip("/").removesuffix(".md")
    hits = [e for e in all_ if e["name"] == q]
    hits = hits or [e for e in all_ if Path(e["name"]).name == q or e["name"].rsplit(".", 1)[0] == q]
    hits = hits or [e for e in all_ if Path(e["name"]).name.rsplit(".", 1)[0] == q]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        die(f"no entry '{q}'. Try: grim find {q.replace('-', ' ').replace('/', ' ')}")
    die(f"'{q}' is ambiguous: " + ", ".join(e["name"] for e in hits))


def line(e):
    return f"{e['name']}{'/' if e['dir'] else ''} — {e['summary'] or '(no summary)'}"


def files(e):
    return sorted(p for p in e["dir"].rglob("*") if p.is_file()) if e["dir"] else []


def score(terms, e, body=True):
    name, tags, summ, use = e["name"].lower(), " ".join(e["tags"]).lower(), e["summary"].lower(), e["use"].lower()
    text = e["body"].lower() if body else ""
    return [5 * (t in name) + 4 * (t in tags) + 3 * (t in summ) + 3 * (t in use) + min(text.count(t), 5) for t in terms]


# --- commands -------------------------------------------------------------------

def cmd_map():
    all_ = entries()
    if not all_ and not shelves():
        return print("grimoire: empty. File the first find with `inscribe new SHELF/NAME ... --new-shelf \"...\"`.")
    print(f"grimoire: {len(all_)} entries. `grim find WORDS` searches, `grim show NAME` reads, `inscribe -h` writes.")
    for s in shelves():
        n = sum(e["shelf"] == s.name for e in all_)
        print(f"  {s.name:<10} {n:>3}  {about(s)}")


def cmd_ls(shelf=None):
    if shelf and not (VAULT / shelf).is_dir():
        die(f"no shelf '{shelf}'. Shelves: " + ", ".join(s.name for s in shelves()))
    cur = None
    for e in entries(shelf):
        if not shelf and e["shelf"] != cur:
            cur = e["shelf"]
            print(f"[{cur}]")
        print(("  " if not shelf else "") + line(e))


def cmd_find(words):
    terms = [w.lower() for w in words if w.strip()]
    if not terms:
        die("usage: grim find WORDS...")
    scored = [(all(p), sum(p), e) for e in entries() if any(p := score(terms, e))]
    if not scored:
        die(f"nothing matches {' '.join(terms)}. `grim ls` lists everything.")
    full = [s for s in scored if s[0]]
    if not full:
        print("(no entry has every word; partial matches)")
    for _, _, e in sorted(full or scored, key=lambda s: -s[1])[:8]:
        print(line(e))
        hits = [(sum(t in l.lower() for t in terms), -i, l) for i, l in enumerate(e["body"].splitlines(), 1)
                if not HEAD.match(l)]
        n, i, l = max(hits, default=(0, 0, ""))
        if n:
            print(f"    {-i}: {l.strip()[:110]}")


def outline(lines):
    heads = [(i, len(m[1]), m[2]) for i, l in enumerate(lines) if (m := HEAD.match(l))]
    for k, (i, lvl, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        print(f"  {'  ' * (lvl - 1)}{title}  ({end - i} lines)")
    return heads


def cmd_show(name, section=None, full=False):
    e = resolve(name)
    lines = e["body"].rstrip("\n").splitlines()
    print(f"== {line(e)}" + (f"  [tags: {', '.join(e['tags'])}]" if e["tags"] else ""))
    if e["use"]:
        print(f"use when: {e['use']}")
    if section:
        heads = [(i, len(m[1]), m[2]) for i, l in enumerate(lines) if (m := HEAD.match(l))]
        hit = next((h for h in heads if section.lower() in h[2].lower()), None)
        if not hit:
            print(f"no section matching '{section}'. Outline:")
            outline(lines)
            sys.exit(1)
        i, lvl, _ = hit
        end = next((j for j, l2, _ in heads if j > i and l2 <= lvl), len(lines))
        shown = "\n".join(lines[i:end])
    elif full or len(lines) <= SHOW_MAX:
        shown = "\n".join(lines)
    elif e["path"].suffix == ".md":
        print(f"({len(lines)} lines, outline only; `grim show {e['name']} -s HEADING` or --full)")
        outline(lines)
        shown = ""
    else:
        shown = "\n".join(lines[:40]) + f"\n... ({len(lines)} lines; --full prints all, or cp \"$(grim path {e['name']})\" DEST)"
    if shown:
        print(shown)
    if e["dir"]:
        fs = [p for p in files(e) if p.name != FOLDER]
        print(f"-- files in {e['dir']}:" if fs else "-- no files besides ENTRY.md")
        for p in fs[:30]:
            print(f"   {p.relative_to(e['dir']).as_posix()}  ({p.stat().st_size // 1024} KB)")
        if len(fs) > 30:
            print(f"   ... {len(fs) - 30} more")
    links = dict.fromkeys(LINK.findall(shown))
    if links:
        all_ = entries()
        print("-- see also:")
        for l in links:
            hit = [x for x in all_ if x["name"] == l or Path(x["name"]).name == l]
            print(f"   {line(hit[0]) if hit else l + ' (missing)'}")


def cmd_run(args):
    ok = "--ok" in args[:1] or (args[1:2] == ["--ok"])
    args = [a for i, a in enumerate(args) if not (a == "--ok" and i < 2)]
    if not args:
        die("usage: grim run [--ok] NAME [ARGS...]")
    e = resolve(args[0])
    main = e["dir"] / "main.py" if e["dir"] else None
    if not main or not main.is_file():
        die(f"{e['name']} is not a tool: tools are folder entries with a main.py")
    rel = e["dir"].relative_to(CLONE).as_posix() if not LOCAL else None
    ran = load("ran.json", {})
    if rel:
        head = git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        since = ran.get(e["name"])
        log = git("log", "--format=%H %ae", *([f"{since}..HEAD"] if since else []), "--", rel).stdout.split()
        foreign = [h for h, mail in zip(log[::2], log[1::2]) if mail != me_email()]
        if foreign and not ok:
            print(f"{e['name']} was changed by someone else since you last ran it. Read it, then run again with --ok:")
            if since:
                diff = git("diff", f"{since}..HEAD", "--", rel).stdout.splitlines()
                print("\n".join(diff[:300]) + (f"\n... ({len(diff) - 300} more diff lines)" if len(diff) > 300 else ""))
            else:
                print(f"(never run here) read the files in {e['dir']}: `grim show {e['name']}`, then the code itself")
            sys.exit(2)
        ran[e["name"]] = head
        save("ran.json", ran)
    cache = _cache_home() / e["name"].replace("/", "-")
    cache.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GRIMOIRE_CACHE": str(cache), "GRIMOIRE_TOOL": str(e["dir"])}
    if "# /// script" in main.read_text(errors="replace"):  # PEP 723 inline dependencies
        if not shutil.which("uv"):
            die(f"{e['name']} declares dependencies and needs uv (https://docs.astral.sh/uv/) to run")
        cmd = ["uv", "run", "--quiet", "--script", str(main), *args[1:]]
    else:
        cmd = [sys.executable, str(main), *args[1:]]
    sys.exit(subprocess.run(cmd, env=env).returncode)


def cmd_me():
    if setting("me", "on") == "off":
        return print("personal memory is off here (`grim config me on` to use it)")
    print(ME.read_text().strip() if ME.exists() else "(no private notes yet: `inscribe me \"...\"` adds one)")


def cmd_init(args):
    url = args[0] if args else os.environ.get("GRIMOIRE_REMOTE")
    if LOCAL:
        die("GRIMOIRE_VAULT is set: that folder is used as is, nothing to clone")
    if ready():
        return print(f"already set up: {CLONE} (upstream {git('remote', 'get-url', 'origin').stdout.strip()})")
    if not url:
        die("usage: grim init URL  (the shared vault's git URL)")
    CLONE.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "-q", url, str(CLONE)], capture_output=True, text=True)
    if r.returncode:
        die(f"could not clone {url}: {r.stderr.strip()}")
    (CLONE / ".git" / "grimoire-pulled").touch()
    save("state.json", {**load("state.json", {}), "seen_head": git("rev-parse", "HEAD").stdout.strip()})
    print(f"vault cloned into {CLONE}; {len(entries())} entries")


def cmd_config(args):
    cfg = load("config.json", {})
    if not args:
        return print(f"me: {cfg.get('me', 'on')}   (state in {STATE})")
    if len(args) != 2 or args[0] != "me" or args[1] not in ("on", "off"):
        die("usage: grim config me on|off")
    cfg["me"] = args[1]
    save("config.json", cfg)
    print(f"me: {args[1]}")


# --- hooks ------------------------------------------------------------------------

def hook_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}


def changed_by_others(since):
    """Entry names that others added or changed upstream after commit `since`."""
    out = git("log", "--format=@@%ae", "--name-only", f"{since}..HEAD", "--", "vault").stdout
    me, names, author = me_email(), [], ""
    for l in out.splitlines():
        if l.startswith("@@"):
            author = l[2:]
        elif l.strip() and author != me:
            parts = Path(l).parts[1:]  # drop "vault"
            if len(parts) >= 2 and not parts[1].startswith(("_", ".")):
                n = "/".join(parts[:2])
                names.append(n.removesuffix(".md") if len(parts) == 2 else n)
    return list(dict.fromkeys(names))


def hook_start():
    hook_input()
    if not ready():
        return print("# grimoire\nThe grimoire plugin is installed but has no vault on this machine. When it fits, ask the "
                     "user for the shared vault's git URL and run `grim init URL` (see the plugin's SETUP.md).")
    sync()
    all_ = entries()
    by = {e["name"]: e for e in all_}
    out = [f"# grimoire: the shared vault ({len(all_)} entries)",
           "Look things up before you build (`grim find WORDS`, `grim show NAME`, `grim run NAME`) and file what you "
           "learn or make with `inscribe` (read the grimoire skill first)."]
    if shelves():
        out.append("Shelves: " + "; ".join(f"{s.name} ({sum(e['shelf'] == s.name for e in all_)}) {about(s)}" for s in shelves()))
    state = load("state.json", {})
    if not LOCAL:
        head = git("rev-parse", "HEAD").stdout.strip()
        since = state.get("seen_head")
        new = [n for n in changed_by_others(since) if n in by] if since and head and since != head else []
        if new:
            out.append("New or changed by others since your last session:")
            out += [f"- {line(by[n])}" for n in new[:8]] + ([f"- ... and {len(new) - 8} more"] if len(new) > 8 else [])
        if head:
            save("state.json", {**state, "seen_head": head})
    if setting("me", "on") != "off" and ME.exists():
        notes = ME.read_text().strip()
        room = START_BUDGET - len("\n".join(out)) - 120
        if notes and room > 200:
            out.append("About the user (private, this machine only; add with `inscribe me \"...\"`):")
            out.append(notes if len(notes) <= room else notes[:room].rsplit("\n", 1)[0] + "\n- ... (`grim me` for all)")
    print("\n".join(out)[:START_BUDGET])


STOP = set("""a about after again all also and any are as at be because been before being but by can could did do
does doing done for from get got had has have how i if in into is it its just like make me more my need no not now
of on one only or our out please really should so some than that the their them then there these they this to too
up use using very want was we what when where which while who why will with would you your""".split())


def hook_prompt():
    hook = hook_input()
    if not ready():
        return
    sync()
    words = re.findall(r"[a-z0-9][a-z0-9_-]{2,}", (hook.get("prompt") or "").lower())
    terms = list(dict.fromkeys(w for w in words if w not in STOP))
    if not terms:
        return
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(hook.get("session_id") or "none"))[:80]
    seen_dir = STATE / "seen"
    seen = set(load(f"seen/{sid}.json", []))
    picks = []
    for e in entries():
        if e["name"] in seen:
            continue
        per = score(terms, e, body=False)
        if sum(x > 0 for x in per) >= 2 or (e["use"] and sum(per) >= 6):
            picks.append((sum(per), e))
    picks = [e for _, e in sorted(picks, key=lambda p: -p[0])[:3]]
    if not picks:
        return
    out = "## grimoire entries that may help (`grim show NAME` to read)\n" + "".join(f"- {line(e)}\n" for e in picks)
    print(out[:PROMPT_BUDGET], end="")
    seen_dir.mkdir(parents=True, exist_ok=True)
    for old in seen_dir.glob("*.json"):  # seen-sets of sessions older than two days
        if time.time() - old.stat().st_mtime > 2 * 86400:
            old.unlink(missing_ok=True)
    save(f"seen/{sid}.json", sorted(seen | {e["name"] for e in picks}))


def main(argv):
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    if cmd in ("-h", "--help", "help"):
        return print(__doc__.strip())
    if cmd == "init":
        return cmd_init(rest)
    if cmd == "config":
        return cmd_config(rest)
    if cmd == "hook":
        return {"start": hook_start, "prompt": hook_prompt}.get(rest[0] if rest else "", lambda: die("usage: grim hook start|prompt"))()
    if cmd == "me":
        return cmd_me()
    sync()
    if not cmd:
        cmd_map()
    elif cmd == "ls":
        cmd_ls(rest[0] if rest else None)
    elif cmd == "find":
        cmd_find(rest)
    elif cmd == "show" and rest:
        sec = rest[rest.index("-s") + 1] if "-s" in rest[:-1] else None
        names = [a for i, a in enumerate(rest) if a not in ("-s", "--full") and not (i and rest[i - 1] == "-s")]
        for n in names:
            cmd_show(n, sec, "--full" in rest)
    elif cmd == "path" and rest:
        e = resolve(rest[0])
        print(e["dir"] or e["path"])
    elif cmd == "run":
        cmd_run(rest)
    else:
        die(__doc__.strip())


if __name__ == "__main__":
    main(sys.argv[1:])

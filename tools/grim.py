#!/usr/bin/python3 -I
"""grim: read the grimoire (the agent's Roblox library) without flooding the context window.

  grim                         the shelves and what each holds
  grim ls [SHELF]              entries with their one-line summaries
  grim find WORDS...           best matches (name, tags, summary, body) with the line that matched
  grim show NAME [-s HEADING]  an entry; a long one prints its outline, -s prints one section, --full all of it
  grim path NAME               absolute path of an entry (copy a snippet file into a project with it)

NAME is shelf/name as `ls` prints it; a bare name works when it is unique. Write with `inscribe`.

The vault lives upstream (the grimoire's git remote). grim reads a private clone that it pulls first, at most
once a minute; inscribe pulls before and pushes after every write. GRIMOIRE_REMOTE sets the upstream (default:
the origin of the repo these tools are in), GRIMOIRE_HOME the clone's folder, GRIMOIRE_VAULT a plain local
folder with no syncing (tests, offline work).
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def _data_home():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "grimoire"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "grimoire"


ROOT = Path(__file__).resolve().parent.parent
LOCAL = os.environ.get("GRIMOIRE_VAULT")  # set: a plain folder, never synced
CLONE = Path(os.environ.get("GRIMOIRE_HOME") or _data_home())
VAULT = Path(LOCAL).resolve() if LOCAL else CLONE / "vault"
FRESH = 60  # seconds a read trusts the last pull
SHOW_MAX = 120  # lines; a longer entry prints its outline unless --full or -s
CODE = {".luau": "--", ".lua": "--", ".py": "#"}  # code entries carry `-- summary:` / `-- tags:` header lines
LINK = re.compile(r"\[\[([^\[\]|#\n]+)(?:[|#][^\]\n]*)?\]\]")  # single-line only: Luau's --[[ ]] isn't a link
HEAD = re.compile(r"^(#{1,6})\s+(.*)")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def warn(msg):
    print(f"grimoire: {msg}", file=sys.stderr)


def git(*args, cwd=None):
    return subprocess.run(["git", "-C", str(cwd or CLONE), *args], capture_output=True, text=True)


def sync(force=False):
    """Pull the upstream vault into the clone (cloning it the first time) and push commits still waiting."""
    if LOCAL:
        return
    if not (CLONE / ".git").is_dir():
        url = os.environ.get("GRIMOIRE_REMOTE") or git("remote", "get-url", "origin", cwd=ROOT).stdout.strip()
        if not url:
            die("grimoire: no upstream known; set GRIMOIRE_REMOTE to the grimoire's git URL")
        CLONE.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", "clone", "-q", url, str(CLONE)], capture_output=True, text=True)
        if r.returncode:
            die(f"grimoire: could not clone {url}: {r.stderr.strip()}")
        (CLONE / ".git" / "grimoire-pulled").touch()
        return
    stamp = CLONE / ".git" / "grimoire-pulled"
    if not force and stamp.exists() and time.time() - stamp.stat().st_mtime < FRESH:
        return
    r = git("pull", "-q", "--rebase")
    if r.returncode:
        git("rebase", "--abort")
        warn(f"couldn't pull, using the last copy ({r.stderr.strip()[:200]})")
    else:
        stamp.touch()
    push()


def push():
    """Push local commits; on a race, rebase onto upstream and retry once. Unpushed commits wait for next time."""
    if LOCAL or git("rev-list", "--count", "@{u}..HEAD").stdout.strip() in ("", "0"):
        return
    if git("push", "-q").returncode == 0:
        return
    if git("pull", "-q", "--rebase").returncode == 0 and git("push", "-q").returncode == 0:
        return
    git("rebase", "--abort")
    warn("saved locally but not pushed yet (offline or no push access); it goes up on the next run")


def shelves():
    if not VAULT.is_dir():  # an empty vault has no folder until its first shelf
        return []
    return sorted(p for p in VAULT.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def about(shelf):
    f = shelf / "_about.md"
    return next((l.strip() for l in f.read_text().splitlines() if l.strip()), "") if f.exists() else ""


def parse(path):
    """-> dict(name, shelf, path, summary, tags, body). Body excludes frontmatter / header lines."""
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
            m = re.match(r"^\s*(?:--|#)\s*(summary|tags):\s*(.*)", line) if i < 10 else None
            if m:
                meta[m[1]] = m[2].strip()
            else:
                keep.append(line)
        body = "".join(keep)
    rel = path.relative_to(VAULT)
    return {
        "name": (rel.with_suffix("") if path.suffix == ".md" else rel).as_posix(),  # "/" on Windows too
        "shelf": rel.parts[0],
        "path": path,
        "summary": meta.get("summary", ""),
        "tags": [t.strip() for t in meta.get("tags", "").strip("[]").split(",") if t.strip()],
        "body": body,
    }


def entries(shelf=None):
    out = []
    for s in shelves():
        if shelf and s.name != shelf:
            continue
        for p in sorted(s.iterdir()):
            if p.is_file() and not p.name.startswith((".", "_")) and (p.suffix == ".md" or p.suffix in CODE):
                out.append(parse(p))
    return out


def resolve(q, all_=None):
    all_ = all_ if all_ is not None else entries()
    q = q.strip().removesuffix(".md")
    hits = [e for e in all_ if e["name"] == q]
    hits = hits or [e for e in all_ if Path(e["name"]).name == q or e["name"].rsplit(".", 1)[0] == q]
    hits = hits or [e for e in all_ if Path(e["name"]).name.rsplit(".", 1)[0] == q]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        die(f"no entry '{q}'. Try: grim find {q.replace('-', ' ').replace('/', ' ')}")
    die(f"'{q}' is ambiguous: " + ", ".join(e["name"] for e in hits))


def line(e):
    return f"{e['name']} — {e['summary'] or '(no summary)'}"


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
    scored = []
    for e in entries():
        name, tags, summ, body = e["name"].lower(), " ".join(e["tags"]).lower(), e["summary"].lower(), e["body"].lower()
        per = [5 * (t in name) + 4 * (t in tags) + 3 * (t in summ) + min(body.count(t), 5) for t in terms]
        if any(per):
            scored.append((all(per), sum(per), e))
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
    print(f"== {e['name']} — {e['summary']}" + (f"  [tags: {', '.join(e['tags'])}]" if e["tags"] else ""))
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
    links = dict.fromkeys(LINK.findall(shown))
    if links:
        all_ = entries()
        print("-- see also:")
        for l in links:
            hit = [x for x in all_ if x["name"] == l or Path(x["name"]).name == l]
            print(f"   {line(hit[0]) if hit else l + ' (missing)'}")


def main(argv):
    if argv[:1] not in (["-h"], ["--help"], ["help"]):
        sync()
    if not argv:
        return cmd_map()
    cmd, rest = argv[0], argv[1:]
    if cmd in ("-h", "--help", "help"):
        print(__doc__.strip())
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
        print(resolve(rest[0])["path"])
    else:
        die(__doc__.strip())


if __name__ == "__main__":
    main(sys.argv[1:])

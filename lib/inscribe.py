"""inscribe: add to the grimoire while you work. Body text comes from stdin.

  inscribe new SHELF/NAME -s "SUMMARY" [-t tag,tag]   a new entry. NAME.md for prose (body starts with '# Title'),
                                                     NAME.luau / .lua / .py for a drop-in code file
      [--use-when "SITUATION"]                       ...makes it a skill: the hooks offer it when that comes up
      [--new-shelf "WHAT IT HOLDS"]                  ...opening a new shelf for it when no existing one fits
  inscribe put SHELF/NAME PATH... [-s "SUMMARY"]      a folder entry (a tool with main.py, an asset set): copy in
      [-t ...] [--use-when ...] [--new-shelf ...]    files or folders; stdin (optional) becomes its ENTRY.md body
  inscribe add NAME [-s HEADING]                     append to an entry, or to the end of one of its sections
  inscribe replace NAME OLD NEW                      replace exact text that occurs once (NEW "" deletes it)
  inscribe meta NAME [-s "SUMMARY"] [-t tag,tag] [--use-when ...]   change an entry's summary, tags or use-when
  inscribe jot "TEXT"                                one dated line in inbox/jots, for a find you have no time to file
  inscribe me "TEXT"                                 a private note about the user: this machine only, never pushed
  inscribe check                                     lint: summaries, broken [[links]], oversized entries and files

The agent shapes the vault: there are no preset shelves. Open one only when no existing shelf fits.
Every write pulls the upstream vault first, then is committed and pushed, so every agent shares one vault.
Files over 5 MB are refused: keep big things local and let a tool make or download them. Read with `grim`.
"""
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grim  # noqa: E402

VAULT = grim.VAULT
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CODE_NAME = re.compile(r"^[A-Za-z0-9]+([-_][A-Za-z0-9]+)*$")
BIG = 300  # lines; split anything longer into separate entries


def die(msg):
    grim.die("inscribe: " + msg)


def stdin_body():
    if sys.stdin.isatty():
        die("give the text on stdin, e.g. a heredoc: inscribe ... <<'EOF'")
    body = sys.stdin.read().strip("\n")
    if not body.strip():
        die("empty text on stdin")
    return body + "\n"


def opt(args, flag):
    if flag in args[:-1]:
        i = args.index(flag)
        val = args[i + 1]
        del args[i : i + 2]
        return val
    return None


def check_summary(s):
    if s is None:
        return
    if not s.strip() or "\n" in s or len(s) > 160:
        die("summary must be one line, 1-160 chars: what it is and when to read it")


def commit(path, msg, *extra):
    rel = path.relative_to(VAULT.parent) if VAULT.parent in path.parents else path
    git, paths = ["git", "-C", str(VAULT)], [str(path), *map(str, extra)]
    ok = subprocess.run(git + ["add", "--", *paths], capture_output=True).returncode == 0
    ok = ok and subprocess.run(git + ["commit", "-q", "-m", f"inscribe: {msg}", "--", *paths],
                               capture_output=True).returncode == 0
    print(f"{'saved' if ok else 'saved (not committed: no git here)'}: {rel}")
    if ok:
        grim.push()


def frontmatter(summary, tags, use=""):
    return f"---\nsummary: {summary}\ntags: {', '.join(tags)}\n" + (f"use-when: {use}\n" if use else "") + "---\n"


def target(spec, shelf_about):
    """Check SHELF/NAME (and a --new-shelf) -> (shelf, fname, about path)."""
    parts = spec.strip("/").split("/")
    if len(parts) != 2:
        die("name is SHELF/NAME (shelves are flat, no subfolders)")
    shelf, fname = parts
    about = VAULT / shelf / "_about.md"
    if shelf_about is not None:
        if (VAULT / shelf).is_dir():
            die(f"shelf '{shelf}' exists; drop --new-shelf")
        if not NAME.match(shelf):
            die(f"bad shelf name '{shelf}': lowercase-kebab-case")
        check_summary(shelf_about)
    elif not (VAULT / shelf).is_dir() or shelf.startswith(("_", ".")):
        die(f"no shelf '{shelf}'. Shelves: " + (", ".join(s.name for s in grim.shelves()) or "none yet")
            + '. If none fits, add --new-shelf "what the shelf holds"')
    return shelf, fname, about


def open_shelf(about, shelf_about):
    if shelf_about is not None:
        about.parent.mkdir(parents=True)
        about.write_text(shelf_about.strip() + "\n")
        return [about]
    return []


def tag_list(t):
    return [x.strip().lower() for x in (t or "").split(",") if x.strip()]


def cmd_new(args):
    summary, tags, shelf_about = opt(args, "-s"), tag_list(opt(args, "-t")), opt(args, "--new-shelf")
    use = opt(args, "--use-when") or ""
    if len(args) != 1 or summary is None:
        die('usage: inscribe new SHELF/NAME -s "SUMMARY" [-t tags] <<EOF ... EOF')
    check_summary(summary)
    check_summary(use or None)
    shelf, fname, about = target(args[0], shelf_about)
    stem, suffix = (fname.rsplit(".", 1) + [""])[:2]
    suffix = "." + suffix if suffix else ".md"
    if suffix != ".md" and suffix not in grim.CODE:
        die(f"entries are .md or {', '.join(grim.CODE)}; put other data in a .md code block")
    if not (NAME if suffix == ".md" else CODE_NAME).match(stem):
        die(f"bad name '{stem}': " + ("lowercase-kebab-case" if suffix == ".md" else "letters, digits, - or _"))
    path = VAULT / shelf / (stem + suffix)
    if path.exists() or (VAULT / shelf / stem).is_dir():
        die(f"{shelf}/{path.name} exists; use `inscribe add` or `replace`")
    clash = [e["name"] for e in grim.entries() if Path(e["name"]).name.rsplit(".", 1)[0] == stem]
    if clash:
        print(f"note: '{stem}' also names {', '.join(clash)}; links to it must use the shelf/ form")
    body = stdin_body()
    extra = open_shelf(about, shelf_about)
    if suffix == ".md":
        if not body.lstrip().startswith("# "):
            body = f"# {stem.replace('-', ' ').capitalize()}\n\n{body}"
        text = frontmatter(summary, tags, use) + "\n" + body
    else:
        c = grim.CODE[suffix]
        text = f"{c} summary: {summary}\n{c} tags: {', '.join(tags)}\n" + (f"{c} use-when: {use}\n" if use else "") + body
    path.write_text(text)
    commit(path, f"new {shelf}/{path.name}" + (" (new shelf)" if extra else ""), *extra)


SKIP = {".git", "__pycache__", ".venv", "node_modules", ".DS_Store"}


def cmd_put(args):
    summary, tags, shelf_about = opt(args, "-s"), opt(args, "-t"), opt(args, "--new-shelf")
    use = opt(args, "--use-when")
    if len(args) < 1:
        die('usage: inscribe put SHELF/NAME PATH... [-s "SUMMARY"] [-t tags] [--use-when ...]')
    check_summary(summary)
    check_summary(use)
    shelf, name, about = target(args[0], shelf_about)
    if not NAME.match(name):
        die(f"bad name '{name}': lowercase-kebab-case")
    folder = VAULT / shelf / name
    if (VAULT / shelf / (name + ".md")).exists():
        die(f"{shelf}/{name}.md is a plain entry; pick another name for the folder")
    entry = folder / grim.FOLDER
    if not entry.exists() and summary is None:
        die(f"{shelf}/{name} is new: give it -s \"what it is; when to use it\"")
    # collect (source, relative destination) and check every size before copying anything
    todo = []
    for src in map(Path, args[1:]):
        if not src.exists():
            die(f"no such file or folder: {src}")
        found = [src] if src.is_file() else [p for p in sorted(src.rglob("*")) if p.is_file()
                                              and not SKIP & set(p.relative_to(src).parts)]
        for f in found:
            todo.append((f, Path(f.name) if src.is_file() else f.relative_to(src)))
    big = [f"{f} ({f.stat().st_size // 1048576} MB)" for f, _ in todo if f.stat().st_size > grim.MAX_FILE]
    if big:
        die("too big for the shared vault (5 MB max): " + ", ".join(big)
            + ". Keep it local; let the tool make or download it into $GRIMOIRE_CACHE.")
    if any(rel.as_posix() == grim.FOLDER for _, rel in todo):
        die(f"{grim.FOLDER} is written by inscribe; give its text on stdin instead")
    body = "" if sys.stdin.isatty() else sys.stdin.read().strip("\n")
    extra = open_shelf(about, shelf_about)
    folder.mkdir(parents=True, exist_ok=True)
    for f, rel in todo:
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, folder / rel)
    if entry.exists():
        e = grim.parse(entry, folder)
        summary, use = summary or e["summary"], use if use is not None else e["use"]
        tag_l = tag_list(tags) if tags is not None else e["tags"]
        body = body or e["body"].strip("\n")
    else:
        tag_l = tag_list(tags)
        run = "\n\nRun: `grim run " + f"{shelf}/{name}" + " [ARGS]`" if (folder / "main.py").exists() else ""
        body = body or f"# {name.replace('-', ' ').capitalize()}{run}"
    if not body.lstrip().startswith("# "):
        body = f"# {name.replace('-', ' ').capitalize()}\n\n{body}"
    entry.write_text(frontmatter(summary, tag_l, use or "") + "\n" + body + "\n")
    commit(folder, f"put {shelf}/{name} ({len(todo)} files)" + (" (new shelf)" if extra else ""), *extra)


def cmd_add(args):
    section = opt(args, "-s")
    if len(args) != 1:
        die("usage: inscribe add NAME [-s HEADING] <<EOF ... EOF")
    e = grim.resolve(args[0])
    body, text = stdin_body(), e["path"].read_text()
    if not section:
        e["path"].write_text(joined(text, body))
    else:
        lines = text.splitlines(keepends=True)
        heads = [(i, len(m[1]), m[2]) for i, l in enumerate(lines) if (m := grim.HEAD.match(l))]
        hit = next((h for h in heads if section.lower() in h[2].lower()), None)
        if not hit:
            die(f"no section matching '{section}' in {e['name']}")
        end = next((j for j, lvl, _ in heads if j > hit[0] and lvl <= hit[1]), len(lines))
        after = "".join(lines[end:])
        e["path"].write_text(joined("".join(lines[:end]), body) + ("\n" + after if after else ""))
    commit(e["path"], f"add to {e['name']}")


def joined(before, body):
    """before + body with a blank line between; none when both sides are list items."""
    last = before.rstrip("\n").rsplit("\n", 1)[-1].lstrip()
    lists = ("- ", "* ")
    sep = "\n" if last.startswith(lists) and body.lstrip().startswith(lists) else "\n\n"
    return before.rstrip("\n") + sep + body


def cmd_replace(args):
    if len(args) != 3:
        die('usage: inscribe replace NAME "OLD" "NEW"')
    e = grim.resolve(args[0])
    text, old, new = e["path"].read_text(), args[1], args[2]
    n = text.count(old)
    if n != 1:
        die(f"OLD occurs {n} times in {e['name']}; it must occur exactly once (quote more of it)")
    e["path"].write_text(text.replace(old, new, 1))
    commit(e["path"], f"edit {e['name']}")


def cmd_meta(args):
    summary, tags, use = opt(args, "-s"), opt(args, "-t"), opt(args, "--use-when")
    if len(args) != 1 or (summary is None and tags is None and use is None):
        die('usage: inscribe meta NAME [-s "SUMMARY"] [-t tag,tag] [--use-when "SITUATION" ("" clears it)]')
    check_summary(summary)
    e = grim.resolve(args[0])
    summary, tags = summary or e["summary"], tag_list(tags) if tags is not None else e["tags"]
    use = use if use is not None else e["use"]
    text = e["path"].read_text()
    if e["path"].suffix == ".md":
        text = frontmatter(summary, tags, use) + "\n" + e["body"]
    else:
        c = grim.CODE[e["path"].suffix]
        rest = [l for l in text.splitlines(keepends=True) if not grim.META.match(l)]
        text = (f"{c} summary: {summary}\n{c} tags: {', '.join(tags)}\n" + (f"{c} use-when: {use}\n" if use else "")
                + "".join(rest))
    e["path"].write_text(text)
    commit(e["path"], f"meta {e['name']}")


def cmd_jot(args):
    if not args:
        die('usage: inscribe jot "TEXT"')
    path, about = VAULT / "inbox" / "jots.md", VAULT / "inbox" / "_about.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not about.exists():
        about.write_text("Unsorted finds jotted mid-task, waiting to be filed. Not verified yet.\n")
    if not path.exists():
        path.write_text(frontmatter("Raw finds jotted mid-task, waiting to be filed into a shelf", ["inbox"])
                        + "\n# Jots\n\n")
    with path.open("a") as f:
        f.write(f"- [{datetime.date.today()}] {' '.join(args).strip()}\n")
    commit(path, "jot", about)


def cmd_me(args):
    if not args:
        die('usage: inscribe me "TEXT"')
    if grim.setting("me", "on") == "off":
        die("personal memory is off on this machine (`grim config me on` to use it)")
    grim.ME.parent.mkdir(parents=True, exist_ok=True)
    with grim.ME.open("a") as f:  # never in the clone, never committed
        f.write(f"- [{datetime.date.today()}] {' '.join(args).strip()}\n")
    print(f"noted privately: {grim.ME}")


def cmd_check(_args):
    all_, bad = grim.entries(), []
    names = {e["name"] for e in all_} | {Path(e["name"]).name for e in all_}
    for e in all_:
        if not e["summary"]:
            bad.append(f"{e['name']}: no summary")
        for link in grim.LINK.findall(e["body"]):
            if link not in names:
                bad.append(f"{e['name']}: broken link [[{link}]]")
        n = e["body"].count("\n")
        if n > BIG:
            bad.append(f"{e['name']}: {n} lines, split it")
        for f in grim.files(e):
            if f.stat().st_size > grim.MAX_FILE:
                bad.append(f"{e['name']}: {f.name} is over 5 MB, keep it local")
    for s in grim.shelves():
        if not (s / "_about.md").exists():
            bad.append(f"shelf {s.name}: no _about.md")
        for d in s.iterdir():
            if d.is_dir() and not d.name.startswith((".", "_")) and not (d / grim.FOLDER).is_file():
                bad.append(f"{s.name}/{d.name}/: folder without {grim.FOLDER}")
    jots = VAULT / "inbox" / "jots.md"
    pending = jots.read_text().count("\n- [") if jots.exists() else 0
    print("\n".join(bad) or f"ok: {len(all_)} entries")
    if pending:
        print(f"{pending} jots in inbox/jots waiting to be filed")
    sys.exit(1 if bad else 0)


def main(argv):
    if argv[:1] not in ([], ["-h"], ["--help"], ["help"], ["me"]):
        grim.sync(force=True)  # write on top of the latest upstream
    cmds = {"new": cmd_new, "put": cmd_put, "add": cmd_add, "replace": cmd_replace, "meta": cmd_meta,
            "jot": cmd_jot, "me": cmd_me, "check": cmd_check}
    if not argv or argv[0] not in cmds:
        print(__doc__.strip())
        sys.exit(0 if argv and argv[0] in ("-h", "--help", "help") else 1)
    cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])

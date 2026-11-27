#!/usr/bin/python3 -I
"""inscribe: add to the grimoire while you work. Body text always comes from stdin.

  inscribe new SHELF/NAME -s "SUMMARY" [-t tag,tag]   a new entry. NAME.md for prose (body starts with '# Title'),
                                                     NAME.luau / .lua / .py for a drop-in code file
      [--new-shelf "WHAT IT HOLDS"]                  ...opening a new shelf for it when no existing one fits
  inscribe add NAME [-s HEADING]                     append to an entry, or to the end of one of its sections
  inscribe replace NAME OLD NEW                      replace exact text that occurs once (NEW "" deletes it)
  inscribe meta NAME [-s "SUMMARY"] [-t tag,tag]     change an entry's summary or tags
  inscribe jot "TEXT"                                one dated line in inbox/jots, for a find you have no time to file
  inscribe check                                     lint: summaries, broken [[links]], oversized entries

The vault grows itself: open a new shelf only when no existing shelf fits (`grim` lists them).
Every write pulls the upstream vault first, then is committed and pushed, so every agent shares one vault.
Read with `grim`.
"""
import datetime
import re
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


def frontmatter(summary, tags):
    return f"---\nsummary: {summary}\ntags: {', '.join(tags)}\n---\n"


def tag_list(t):
    return [x.strip().lower() for x in (t or "").split(",") if x.strip()]


def cmd_new(args):
    summary, tags, shelf_about = opt(args, "-s"), tag_list(opt(args, "-t")), opt(args, "--new-shelf")
    if len(args) != 1 or summary is None:
        die('usage: inscribe new SHELF/NAME -s "SUMMARY" [-t tags] <<EOF ... EOF')
    check_summary(summary)
    parts = args[0].strip("/").split("/")
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
        die(f"no shelf '{shelf}'. Shelves: " + ", ".join(s.name for s in grim.shelves())
            + '. If none fits, add --new-shelf "what the shelf holds"')
    stem, suffix = (fname.rsplit(".", 1) + [""])[:2]
    suffix = "." + suffix if suffix else ".md"
    if suffix != ".md" and suffix not in grim.CODE:
        die(f"entries are .md or {', '.join(grim.CODE)}; put other data in a .md code block")
    if not (NAME if suffix == ".md" else CODE_NAME).match(stem):
        die(f"bad name '{stem}': " + ("lowercase-kebab-case" if suffix == ".md" else "letters, digits, - or _"))
    path = VAULT / shelf / (stem + suffix)
    if path.exists():
        die(f"{shelf}/{path.name} exists; use `inscribe add` or `replace`")
    clash = [e["name"] for e in grim.entries() if Path(e["name"]).name.rsplit(".", 1)[0] == stem]
    if clash:
        print(f"note: '{stem}' also names {', '.join(clash)}; links to it must use the shelf/ form")
    body = stdin_body()
    if shelf_about is not None:
        about.parent.mkdir()
        about.write_text(shelf_about.strip() + "\n")
    if suffix == ".md":
        if not body.lstrip().startswith("# "):
            body = f"# {stem.replace('-', ' ').capitalize()}\n\n{body}"
        text = frontmatter(summary, tags) + "\n" + body
    else:
        c = grim.CODE[suffix]
        text = f"{c} summary: {summary}\n{c} tags: {', '.join(tags)}\n" + body
    path.write_text(text)
    commit(path, f"new {shelf}/{path.name}" + (" (new shelf)" if shelf_about is not None else ""),
           *([about] if shelf_about is not None else []))


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
    summary, tags = opt(args, "-s"), opt(args, "-t")
    if len(args) != 1 or (summary is None and tags is None):
        die('usage: inscribe meta NAME [-s "SUMMARY"] [-t tag,tag]')
    check_summary(summary)
    e = grim.resolve(args[0])
    summary, tags = summary or e["summary"], tag_list(tags) if tags is not None else e["tags"]
    text = e["path"].read_text()
    if e["path"].suffix == ".md":
        text = frontmatter(summary, tags) + "\n" + e["body"]
    else:
        c = grim.CODE[e["path"].suffix]
        rest = [l for l in text.splitlines(keepends=True) if not re.match(rf"^\s*{re.escape(c)}\s*(summary|tags):", l)]
        text = f"{c} summary: {summary}\n{c} tags: {', '.join(tags)}\n" + "".join(rest)
    e["path"].write_text(text)
    commit(e["path"], f"meta {e['name']}")


def cmd_jot(args):
    if not args:
        die('usage: inscribe jot "TEXT"')
    path = VAULT / "inbox" / "jots.md"
    if not path.exists():
        path.write_text(frontmatter("Raw finds jotted mid-task, waiting to be filed into a shelf", ["inbox"])
                        + "\n# Jots\n\n")
    with path.open("a") as f:
        f.write(f"- [{datetime.date.today()}] {' '.join(args).strip()}\n")
    commit(path, "jot")


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
    for s in grim.shelves():
        if not (s / "_about.md").exists():
            bad.append(f"shelf {s.name}: no _about.md")
    jots = VAULT / "inbox" / "jots.md"
    pending = jots.read_text().count("\n- [") if jots.exists() else 0
    print("\n".join(bad) or f"ok: {len(all_)} entries")
    if pending:
        print(f"{pending} jots in inbox/jots waiting to be filed")
    sys.exit(1 if bad else 0)


def main(argv):
    if argv[:1] not in ([], ["-h"], ["--help"], ["help"]):
        grim.sync(force=True)  # write on top of the latest upstream
    if not VAULT.is_dir():
        die(f"no vault at {VAULT}")
    cmds = {"new": cmd_new, "add": cmd_add, "replace": cmd_replace, "meta": cmd_meta, "jot": cmd_jot, "check": cmd_check}
    if not argv or argv[0] not in cmds:
        print(__doc__.strip())
        sys.exit(0 if argv and argv[0] in ("-h", "--help", "help") else 1)
    cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])

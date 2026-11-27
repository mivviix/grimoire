# grimoire (maintenance sessions)

The agent's Roblox library. Sessions *in this folder* change how it works; everywhere else agents only use it.

- `vault/`: the content. One folder per shelf, flat (no subfolders). Each shelf has `_about.md` (first line =
  its description in `grim`). Entries are `name.md` with frontmatter (`summary:`, `tags:`) or code files
  (`.luau/.lua/.py`) with `-- summary:` / `-- tags:` header lines. Links are `[[name]]` or `[[shelf/name]]`.
- `tools/grim.py`: read CLI (map, ls, find, show with outline/sections, path). Built to keep context small:
  long entries print an outline, find prints 8 hits with one matching line each.
- `tools/inscribe.py`: write CLI (new, add, replace, meta, jot, check). Opens a new shelf only with
  `--new-shelf "description"` alongside its first entry; commits and pushes every write
  (`git commit -- <file>`), messages start with `inscribe:`.
- The vault ships empty (the starter shelves' `_about.md` only) and is filled by agents as they work.
- `tools/skill/SKILL.md`: what agents are told. `tools/install.sh` (Linux/macOS) symlinks both commands
  into ~/.local/bin and the skill into ~/.claude/skills/grimoire. `tools/install.bat` (Windows, no admin)
  writes `grim.cmd` / `inscribe.cmd` launchers (`py -3 -X utf8`) into %USERPROFILE%\.local\bin, adds it to the
  user PATH, and junctions the skill. Keep the two installers doing the same thing; `.bat` stays CRLF
  (`.gitattributes`).
- Cross-platform: entry names always use `/` (`as_posix`); vault files are UTF-8 (Windows runs with `-X utf8`).
- `tools/test_grimoire.py`: self-check against a temp vault: `python3 tools/test_grimoire.py` (also syncs two
  fake machines through a local bare repo).

Stdlib Python only, no venv.

## The vault lives upstream

The vault's truth is the git remote (GitHub), never a local folder. The tools don't read this checkout's
`vault/`: they keep a private clone (`~/.local/share/grimoire`, `%LOCALAPPDATA%\grimoire` on Windows,
`GRIMOIRE_HOME` to move it), `grim` pulls it at most once a minute, and `inscribe` pulls before every write
and pushes after it. A push that fails (offline, race, no access) stays committed in the clone and goes up
on the next run; nothing is dropped. Upstream is `GRIMOIRE_REMOTE`, else this repo's `origin`. Keep it so:
- Any new read or write path goes through `grim.sync()` / `grim.push()`; nothing writes the vault in place.
- In a maintenance session, `git pull` before touching `vault/` here: agents push to it all the time.
- `GRIMOIRE_VAULT=<folder>` is the only unsynced mode (tests, offline experiments).
- Someone without push access to this repo uses their own fork: clone the fork, or set `GRIMOIRE_REMOTE`.

## Distributable to anyone

The project must always work for anyone who clones it, on any machine, with nothing but git and Python 3.11+.
Every change keeps it that way:
- No paths, usernames, accounts or machine facts from one person's setup in code, docs, the skill or the
  vault. Paths are relative to the repo (`tools/` finds `vault/` by itself) or come from env vars.
- No dependency on anyone's private tools or other projects. A tool may be mentioned as optional
  ("if X is installed"), never required.
- Stdlib Python only; `tools/install.sh` / `tools/install.bat` stay the one setup step, and touch only
  user-level paths.
- The vault holds general Roblox knowledge, never one person's preferences, projects or private notes:
  those belong in that person's own memory or project notes.
- The layout stays self-explanatory: this file, the skill and `grim -h` / `inscribe -h` are enough to use
  and maintain it without asking anyone.

Upkeep: file `vault/inbox/jots.md` lines into shelves, merge overlapping entries, run `inscribe check`.
Merge or rename shelves that agents opened badly (move files, fix `[[links]]`, `inscribe check`).

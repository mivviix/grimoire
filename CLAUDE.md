# grimoire (maintenance sessions)

The agent's Roblox library. Sessions *in this folder* change how it works; everywhere else agents only use it.

- `vault/`: the content. One folder per shelf, flat (no subfolders). Each shelf has `_about.md` (first line =
  its description in `grim`). Entries are `name.md` with frontmatter (`summary:`, `tags:`) or code files
  (`.luau/.lua/.py`) with `-- summary:` / `-- tags:` header lines. Links are `[[name]]` or `[[shelf/name]]`.
- `tools/grim.py`: read CLI (map, ls, find, show with outline/sections, path). Built to keep context small:
  long entries print an outline, find prints 8 hits with one matching line each.
- `tools/inscribe.py`: write CLI (new, add, replace, meta, jot, check). Opens a new shelf only with
  `--new-shelf "description"` alongside its first entry; commits every write to this repo
  (`git commit -- <file>`), messages start with `inscribe:`.
- The vault ships empty (the starter shelves' `_about.md` only) and is filled by agents as they work.
- `tools/skill/SKILL.md`: what agents are told. `tools/install.sh` symlinks both commands into ~/.local/bin
  and the skill into ~/.claude/skills/grimoire.
- `tools/test_grimoire.py`: self-check against a temp vault: `python3 tools/test_grimoire.py`.

Stdlib Python only, no venv. `GRIMOIRE_VAULT` points the tools at another vault (tests use it).

## Distributable to anyone

The project must always work for anyone who clones it, on any machine, with nothing but git and Python 3.11+.
Every change keeps it that way:
- No paths, usernames, accounts or machine facts from one person's setup in code, docs, the skill or the
  vault. Paths are relative to the repo (`tools/` finds `vault/` by itself) or come from env vars.
- No dependency on anyone's private tools or other projects. A tool may be mentioned as optional
  ("if X is installed"), never required.
- Stdlib Python only; `tools/install.sh` stays the one setup step, and touches only user-level paths.
- The vault holds general Roblox knowledge, never one person's preferences, projects or private notes:
  those belong in that person's own memory or project notes.
- The layout stays self-explanatory: this file, the skill and `grim -h` / `inscribe -h` are enough to use
  and maintain it without asking anyone.

Upkeep: file `vault/inbox/jots.md` lines into shelves, merge overlapping entries, run `inscribe check`.
Merge or rename shelves that agents opened badly (move files, fix `[[links]]`, `inscribe check`).

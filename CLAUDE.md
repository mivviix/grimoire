# grimoire (maintenance sessions)

The agent's Roblox library. Sessions *in this folder* change how it works; everywhere else agents only use it.

- `vault/`: the content. One folder per shelf, flat (no subfolders). Each shelf has `_about.md` (first line =
  its description in `grim`). Entries are `name.md` with frontmatter (`summary:`, `tags:`) or code files
  (`.luau/.lua/.py`) with `-- summary:` / `-- tags:` header lines. Links are `[[name]]` or `[[shelf/name]]`.
- `tools/grim.py`: read CLI (map, ls, find, show with outline/sections, path). Built to keep context small:
  long entries print an outline, find prints 8 hits with one matching line each.
- `tools/inscribe.py`: write CLI (new, add, replace, meta, jot, check). Refuses new shelves; commits every
  write to this repo (`git commit -- <file>`), messages start with `inscribe:`.
- `tools/skill/SKILL.md`: what agents are told. `tools/install.sh` symlinks both commands into ~/.local/bin
  and the skill into ~/.claude/skills/grimoire.
- `tools/test_grimoire.py`: self-check against a temp vault: `python3 tools/test_grimoire.py`.

Stdlib Python only, no venv. `GRIMOIRE_VAULT` points the tools at another vault (tests use it).

Upkeep: file `vault/inbox/jots.md` lines into shelves, merge overlapping entries, run `inscribe check`.
Adding a shelf = `mkdir vault/NAME` + `_about.md`, and mention it in the skill.

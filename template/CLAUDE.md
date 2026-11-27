# This folder is a grimoire vault

This repo is a shared library that agents build while they work and that users train by feeding it: lessons,
guides, skills, snippets, runnable tools and small assets, all in `vault/`. Everyone on it gets every addition
as soon as it is saved. It may be open on someone's PC (with their local tools: Roblox Studio, MCPs,
PowerShell) or in a cloud session from their phone (just the vault). Both work on the same GitHub repo.

- Read the vault with `grim` (`grim find WORDS`, `grim show NAME`, `grim skills`, `grim run NAME`). The session
  start lists the shelves and the vault's skills: when a skill's description fits the task, `grim show` it.
- Save with `inscribe`: it pulls first, then commits and pushes each save to GitHub at once. Read `grim guide`
  before your first save in a session. Don't hand-edit or hand-commit files in `vault/`.
- When the user wants to train the vault (teach it what they know), run `grim guide train` and follow it.
- If `grim` or `inscribe` isn't found: `python3 .grimoire/run.py grim ...` (or `python`, `py -3` on Windows).
- `vault/` is shared: nothing about one person goes in it. `inscribe me "..."` keeps notes about the user
  private on this machine.
- Use plain words with the user, no technical jargon unless they ask.
- `.grimoire/`, `.claude/`, `.grimoire-vault` and this file are grimoire's setup: leave them alone unless the
  user asks. How grimoire itself works changes in the grimoire repo, not here.

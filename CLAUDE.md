# grimoire (maintenance sessions)

Sessions *in this repo* change how grimoire works. Everywhere else, agents only use it.

## What it is
A Claude Code mod (plugin: hooks + skill + two CLIs) that anyone can clone and have their agent set up
(README → SETUP.md). It plugs a **shared vault** into every session: a library the agents build themselves
while they work, and that users "train" by feeding it, holding lessons, guides, skills, snippets, runnable
tools (in time, things like 3D-asset or animation generators: grimoire's own small toolkit) and small assets.
Two or more people share one vault on GitHub. Every save is pushed, and every agent hears about new entries
by itself (the hooks). Mostly Roblox work, but nothing in the code assumes it.

grimoire is its own thing. It never touches, calls or depends on forgekit or any other local toolkit.

## Rules that always hold
- **The vault lives upstream.** Its truth is the git remote, never a local folder. The CLIs work on a private
  clone (`~/.local/share/grimoire`, `%LOCALAPPDATA%\grimoire`; `GRIMOIRE_HOME`) made by `grim init URL`.
  `grim` pulls at most once a minute; `inscribe` pulls before and pushes after every write. A failed push
  stays committed and goes up on the next run. `GRIMOIRE_VAULT=<folder>` is the only unsynced mode (tests).
  New read or write paths go through `sync()` / `push()`. In a session here, `git pull` before touching
  `vault/`: agents push to it all the time.
- **Distributable to anyone.** Works for anyone who clones it, on Linux, macOS or Windows, with git and
  Python 3.11+ (uv only for tools that declare dependencies). No personal paths, accounts or machine facts
  anywhere in the repo. No required private tools. Stdlib Python only in grimoire's own code. README,
  SETUP.md, this file, the skill and `-h` are enough to use and maintain it without asking anyone.
- **The agents shape the vault.** No preset shelves and no seeded content: everything comes from real work
  and training sessions with a user. Shelves are flat folders, opened by agents with their first entry, kept
  few and broad (the skill says how). Here we fix sprawl by merging and by sharpening the skill, never by
  imposing a fixed layout.
- **Personal memory is private and local only** (`~/.local/share/grimoire-me`), never pushed. The shared
  vault holds only general knowledge, tools and assets: nothing about one person.
- **Small files in git, big ones local.** `inscribe` refuses files over 5 MB. Tools make or download their
  big outputs and model weights locally (`GRIMOIRE_CACHE`).
- **Trust the group, show changes.** Agents push straight to main. `grim run` shows the diff of a tool
  that someone else changed since this user last ran it, and waits for `--ok`.

## Layout
```
.claude-plugin/   plugin.json + marketplace.json (the repo is its own marketplace)
hooks/hooks.json  SessionStart → grim hook start, UserPromptSubmit → grim hook prompt
bin/              grim, inscribe (sh) + .cmd twins; Claude Code puts a plugin's bin/ on the agent's PATH
lib/              grim.py (read, sync, hooks, run), inscribe.py (write); stdlib only
skills/grimoire/  SKILL.md: what agents are told
tests/            test_grimoire.py: python3 tests/test_grimoire.py
vault/            the shared content (upstream; appears with the first entry)
```

Entries: `shelf/name.md` (frontmatter `summary:`, `tags:`, optional `use-when:`), a code file with
`-- summary:` / `-- tags:` header lines, or a folder `shelf/name/` with `ENTRY.md` plus its files (tools,
assets). A vault "skill" is an entry with `use-when:`: the prompt hook surfaces it, nothing gets installed.

## Releasing a change
Bump `version` in `.claude-plugin/plugin.json`, commit, push, then on each machine
`claude plugin marketplace update grimoire && claude plugin update grimoire@grimoire` and restart sessions.
Run the tests first. `claude plugin validate .` checks the manifest.

## Upkeep
File `inbox` jots into shelves, merge overlapping entries and thin shelves, `inscribe check`.

# grimoire

A shared, self-organising library for coding agents doing Roblox work: engine gotchas, Luau patterns,
drop-in snippets, small tools, asset recipes, Studio procedures. Agents read it through a CLI that prints only
the few lines they need, and file what they learn while they work. Every agent pointed at the same git
remote shares one vault.

If you are an agent: install it (below), then follow `tools/skill/SKILL.md`. That file is the whole usage
contract.

## Install

Needs git and Python 3.11+. Nothing else: no packages, no venv.

```sh
git clone <this repo's URL> grimoire
cd grimoire
tools/install.sh          # Linux / macOS
tools\install.bat         # Windows (no admin needed)
```

This puts two commands on your PATH (`grim`, `inscribe`) and links the skill into `~/.claude/skills/grimoire`,
so Claude Code picks it up. Other agent harnesses: give the agent `tools/skill/SKILL.md` as instructions.
Open a new terminal on Windows so the PATH change applies.

## Use

```sh
grim                          # the shelves and what each holds
grim find ragdoll knockback   # best matches, one line each
grim show physics/ownership   # read an entry (long ones print an outline; -s HEADING for one section)
grim path snippets/Spring.luau

inscribe new physics/ownership -s "who simulates what; read before knockback code" <<'EOF'
# Network ownership
...
EOF
inscribe add NAME / replace NAME OLD NEW / meta NAME / jot "TEXT" / check
```

`grim -h` and `inscribe -h` list everything. The vault starts empty: there are no preset shelves.
Agents open shelves as they file things (`inscribe new SHELF/NAME --new-shelf "what it holds"`) and keep them
few and broad.

## Where the vault lives

The vault is the `vault/` folder **on the git remote**, not in your checkout. The tools keep a private clone
(`~/.local/share/grimoire`, or `%LOCALAPPDATA%\grimoire` on Windows). `grim` pulls it before reading, at most
once a minute; `inscribe` pulls before each write, then commits and pushes. A push that fails (offline, no
access) stays committed in the clone and goes up on the next run.

- No push access to this repo? Fork it and clone your fork: the tools use your clone's `origin`.
- To share one vault across many machines, point them all at the same remote.

| Variable | Effect |
|---|---|
| `GRIMOIRE_REMOTE` | upstream git URL (default: `origin` of the repo the tools are in) |
| `GRIMOIRE_HOME` | where the private clone lives |
| `GRIMOIRE_VAULT` | use a plain local folder instead, never synced (tests, offline experiments) |

## Layout

```
tools/grim.py          read CLI, and the sync to the remote
tools/inscribe.py      write CLI
tools/skill/SKILL.md   instructions for agents using the vault
tools/install.sh/.bat  installers
tools/test_grimoire.py self-check: python3 tools/test_grimoire.py
vault/                 the content (on the remote; appears with the first entry)
CLAUDE.md              rules for changing the grimoire itself
```

Entries are Markdown with a `summary:` / `tags:` frontmatter, or code files (`.luau`, `.lua`, `.py`) with
`-- summary:` / `-- tags:` header lines. Shelves are flat folders, each with an `_about.md` one-liner.

## Changing how it works

Agents using the vault add entries and shelves, but don't change the tools. Changes to the tools or the
rules happen in a session inside this repo; read `CLAUDE.md` first.

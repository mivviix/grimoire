---
name: grimoire
description: The grimoire is a shared vault that agents build for themselves - lessons, guides, skills, snippets, runnable tools and small assets, mostly for Roblox work - read with `grim` and grown with `inscribe`, synced through git with everyone on the same vault. Use before building or making anything (look up what exists, run a tool instead of rewriting it) and whenever you learn, fix or build something reusable (file it), or the user wants to teach or "train" the vault.
---

# grimoire

A library you and other agents build while working, shared through git: what one agent files, every agent on
the same vault gets. Read it through `grim` so you only load the lines you need; never `cat` or glob a vault
folder yourself. The hooks already show you the shelves and what's new at session start, and relevant entries
with each message. If `grim` or `inscribe` warn that they couldn't pull or push, carry on: they retry.

## Read: `grim`
- `grim find WORDS...`: best matches with summaries. Start any task here with 2-4 words from it.
- `grim show NAME [NAME...]`: read entries; a long one prints its outline, then `-s HEADING`. A folder entry
  (tool, asset set) also lists its files.
- `grim run NAME [ARGS]`: run a tool entry. If someone else changed it since you last ran it, grim prints the
  diff and stops: read it, and only if it does what it claims, run again with `--ok`. Never `--ok` blindly.
- `grim`, `grim ls SHELF`, `grim path NAME` (copy a snippet or asset into a project), `grim me`.

What the vault says was learned the hard way; prefer it over your memory, unless the official docs disagree
(then fix the entry). `inbox` is unverified.

## Write: `inscribe`
File it when it cost real effort or will save the next agent a mistake: a confirmed behaviour, a fix that
worked, a procedure, a pattern that held up, a module, a tool you built, an asset recipe that came out well.
Not: guesses, what the docs say plainly, or anything about one person or project (see "the user" below).
`grim find` first, and add to an existing entry before making a new one.

- Prose or a code file: `inscribe new SHELF/NAME -s "what it is; when to read it" -t tag,tag <<'EOF' ... EOF`
  (`NAME.md` kebab-case, starts with `# Title`; code is `Name.luau` / `.lua` / `.py`).
- A **skill** (a how-to the agent should reach for in a situation): add `--use-when "making X / when Y"`.
  The hooks offer it whenever that comes up; nothing needs installing.
- A **tool**: build it in a scratch folder with a `main.py` entry point (stdlib, or PEP 723 inline
  `# /// script` dependencies, which run through uv). It takes arguments, writes outputs to the current folder
  or a path it is given, and puts downloads (model weights etc.) in `$GRIMOIRE_CACHE`. Then
  `inscribe put SHELF/NAME DIR -s "..." --use-when "..." <<'EOF'` with an ENTRY.md body that says how to run it,
  what it needs (GPU, uv, disk) and what it outputs. Re-run `put` to update it.
- **Assets** (a texture, a model, a sound under 5 MB): `inscribe put SHELF/NAME FILES...`. Bigger files stay
  local: share the tool or recipe that makes them instead.
- Edit: `inscribe add NAME [-s HEADING]`, `inscribe replace NAME "old" "new"`, `inscribe meta NAME ...`.
- No time to file it properly: `inscribe jot "one line: what, and how you know"`.
- Link related entries with `[[name]]`; run `inscribe check` after bigger edits.

Style: facts first, short lines, the why in a few words. A summary says what it holds and when to read it.
Keep entries under ~150 lines; split by topic instead.

## Training sessions
When the user wants to teach the vault ("remember this", "feed it this", "make a tool for X"), you are
building the library with them: turn what they give you into entries, skills and tools in the shapes above,
test a tool once, and file it. Ask what it should be used for, so the `--use-when` is right.

## The user
Things about the user (preferences, how they work, their projects) never go in the shared vault: other people
read it. Keep them private with `inscribe me "..."` (this machine only, never pushed; shown at session start).
If personal memory is off (`grim config`), the user has another memory system: use that.

## Shelves are yours to shape
There are no preset shelves: you decide them as the vault fills. Open one with the entry that needs it:
`inscribe new physics/network-ownership -s "..." --new-shelf "how Roblox physics really behaves"`.
- Few broad shelves beat many narrow ones. A handful is plenty for a long time. Don't open a shelf for one
  entry, don't split a shelf to look organised, and never make a shelf per project or per day.
- Put it in the shelf it most nearly fits; a new shelf is for a topic that clearly stands apart.
- Short lowercase kebab-case names that say the topic plainly (`physics`, `ui`, `tools`).
- `inscribe jot` opens `inbox` by itself; file its lines into real shelves when you have a moment.

You may add entries, tools and shelves. You may not change grimoire itself (its CLIs, hooks, or how the vault
works): that happens in a session inside the grimoire repo. If the structure gets in your way, tell the user.

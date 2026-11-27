---
name: grimoire
description: The grimoire is the agent's Roblox library - engine gotchas, Luau idioms, system patterns, drop-in snippets, asset-making recipes and Studio procedures - read with `grim` and grown with `inscribe`. Use at the start of any Roblox coding, Studio or asset-creation task (look up what is already known before writing code or making an asset), and whenever you learn something reusable about Roblox while working (file it).
---

# grimoire

A library of what is known about making Roblox games here. It is read through a command so you only load the
few lines you need: never `cat` or glob the vault folder yourself.

## Read: `grim`
- `grim`: the shelves (engine, luau, patterns, snippets, assets, guides, inbox) and their size.
- `grim find WORDS...`: the best matches with their summaries. Start every Roblox task here with 2-4 words
  from the task ("ragdoll knockback", "datastore save", "streaming teleport").
- `grim show NAME [NAME...]`: read entries. A long one prints its outline: then `grim show NAME -s HEADING`.
- `grim ls SHELF`: everything on one shelf.
- `grim path NAME`: the file, to copy a snippet into a project: `cp "$(grim path Cleanup.luau)" src/shared/`.

What the grimoire says is confirmed knowledge; prefer it over your own memory of the Roblox API when they
disagree, unless the official docs say otherwise (then fix the entry). `inbox/` is unverified.
For forgekit flags and formats read `forgekit help <tool>`; the grimoire only maps which tool to use.

## Write: `inscribe`
File a find when it cost real effort or would save the next agent a mistake: an engine behaviour you
confirmed, a fix that worked, a pattern that held up, a reusable module, an asset recipe that came out well.
Not: project-specific details (they go in that project's own notes), guesses, or what the docs say plainly.

- Check first: `grim find` the topic. Add to an existing entry before making a new one.
- New entry, body on stdin: `inscribe new SHELF/NAME -s "what it is; when to read it" -t tag,tag <<'EOF' ... EOF`.
  Prose is `NAME.md` (kebab-case, body starts with `# Title`); code is `Name.luau`.
- Add: `inscribe add NAME [-s HEADING] <<'EOF' ... EOF`. Fix: `inscribe replace NAME "old" "new"`.
  Summary/tags: `inscribe meta NAME -s "..." -t ...`.
- No time to file it properly: `inscribe jot "one line: what, and how you know"`.
- Link related entries with `[[name]]`. Run `inscribe check` after bigger edits.

Style: facts first, short lines, the why in a few words, code only where it says more than prose. A summary
says what the entry holds and when to read it. Keep entries under ~150 lines; split by topic instead.

You may add and edit entries. You may not add shelves or change the tools: that is the user's call, made in
a session in ~/Documents/grimoire. If the structure gets in your way, say so to the user.

---
description: Train the shared grimoire vault - turn what the user already knows or has (notes, files, pastes, how they do things) into vault entries, skills and tools
argument-hint: "[what to teach, or files/folders to read]"
---

The user wants to train the shared grimoire vault: give it what they already know so every agent on the vault
gets it. Read the grimoire skill first if you haven't this session. Material to start from: $ARGUMENTS

Use plain words with the user: no technical jargon unless they ask for it.

1. **Gather.** If nothing was given, ask what they want to teach: files or folders to read, notes to paste, or
   just talk it through with you. Read files yourself; don't make them retype what's on disk.
2. **Go through it piece by piece.** For each topic decide what it becomes:
   - a **lesson or guide** (`inscribe new`): facts, gotchas, a reference.
   - a **skill** (`inscribe skill`): a procedure an agent should follow when a situation comes up. Its
     description is all an agent sees until it opens the skill, so it says what the skill does and when to use
     it, with the words an agent would have in mind at that moment. The body is the full instructions; put
     long references or scripts beside it as files.
   - a **tool** (`inscribe put` with a `main.py`): something that should run, not be re-typed. Test it once.
   - a **snippet or asset** (`inscribe new` / `inscribe put`).
   `grim find` before each one, and add to or improve an existing entry or skill instead of duplicating it.
3. **Ask when it matters, not for every line:** what a skill is really for, what's verified versus a hunch
   (hunches go to `inscribe jot`, or get left out), and anything you'd otherwise guess. Ask about several
   pieces at once.
4. **Keep it general.** The vault is shared: nothing about one person (their preferences, accounts, private
   projects, secrets). Strip it out, or keep it private with `inscribe me` if they want it remembered.
5. **Wrap up** with a short list of what you filed (names, one line each) and what you left out and why.
   `inscribe check` at the end.

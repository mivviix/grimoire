# Setting up grimoire (for the agent)

grimoire is a shared vault on GitHub that agents read with `grim` and grow with `inscribe`. Every save goes to
GitHub at once. Do these steps, asking the user only where it says so. Same on Linux, macOS and Windows.

1. **Check tools.** `git --version` and Python 3.11+ (`python3 --version`, or `python` / `py -3` on Windows).
   Optional: `uv` (some vault tools need it); offer to install it if missing. Make sure git can push to
   GitHub (for example `gh auth login`); leave passwords and tokens to the user.
2. **Which vault?** Ask for the vault repo's URL (they need push access to it). A brand-new, empty repo is
   fine: step 3 sets it up.
3. **The vault folder (the main way in).** Ask where they want it, then `git clone VAULT_URL FOLDER`. If the
   clone has no `.grimoire-vault` file yet, set it up once from a clone of this repo:
   `cd FOLDER && python3 <grimoire clone>/lib/grim.py scaffold`. From now on, opening Claude in that folder
   (on the PC, or a cloud session on the same repo from their phone) is all they need: saves go to GitHub,
   and on the PC their own tools (Roblox Studio, MCPs, PowerShell) work as usual.
4. **Optional: the plugin**, to use the vault from sessions in *other* folders too (their game projects).
   ```
   claude plugin marketplace add SOURCE      # SOURCE = this repo's GitHub owner/repo, or a local clone
   claude plugin install grimoire@grimoire
   <grimoire clone>/bin/grim init VAULT_URL  # Windows: <grimoire clone>\bin\grim.cmd init VAULT_URL
   ```
5. **Personal memory.** Ask: "Do you already use a memory system for Claude (one that remembers you)?" If yes:
   `grim config me off` (run from the vault folder: `python3 .grimoire/run.py grim config me off`).
6. **Permissions (ask first).** Offer to add `"Bash(grim *)"`, `"Bash(inscribe *)"` and
   `"Bash(python3 .grimoire/run.py *)"` to `permissions.allow` in `~/.claude/settings.json`.
7. **Done.** Tell them to start a new session in the vault folder. Its start shows a short "grimoire" block.
   To feed the vault what they already know: `/grimoire:train` with the plugin, or just "let's train the vault".

Updating: the vault folder fetches the newest tools by itself. The plugin:
`claude plugin marketplace update grimoire && claude plugin update grimoire@grimoire`.

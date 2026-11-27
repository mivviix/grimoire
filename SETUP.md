# Setting up grimoire (for the agent)

You are installing grimoire for your user: a Claude Code plugin plus a shared vault on git. Do these steps,
asking the user only where it says so. Works the same on Linux, macOS and Windows.

1. **Check tools.** `git --version` and Python 3.11+ (`python3 --version`, or `python`/`py -3` on Windows).
   Optional: `uv` (some vault tools need it for their dependencies); offer to install it if missing.
2. **Which vault?** Ask the user for the vault's git URL: the repo they were invited to (needs push
   access) or their own fork of this repo. Default: this repo's URL if they have push access.
3. **Install the plugin** (`SOURCE` = the GitHub `owner/repo` or the path of a local clone):
   ```
   claude plugin marketplace add SOURCE
   claude plugin install grimoire@grimoire
   ```
4. **Make the vault clone.** The plugin's `grim` reaches PATH only in the next session, so now run it from a
   clone of this repo (`git clone` it to a temporary folder if you don't have one): `<clone>/bin/grim init
   VAULT_URL` (Windows: `<clone>\bin\grim.cmd init VAULT_URL`). It clones the vault into the user's data
   folder. If pushing will need a login, make sure git is signed in (for GitHub: `gh auth login` or a
   credential helper); leave passwords and tokens to the user.
5. **Personal memory.** Ask: "Do you already use a memory system for Claude (one that remembers you)?"
   If yes: `<clone>/bin/grim config me off`. If no, leave it on: grimoire keeps a small private memory about
   them on this machine only; it is never pushed.
6. **Permissions (ask first).** Offer to add `"Bash(grim *)"` and `"Bash(inscribe *)"` to
   `permissions.allow` in `~/.claude/settings.json`, so lookups don't prompt every time.
7. **Done.** Tell the user to start a new session. Its start should show a short "grimoire" block, and
   `grim` should print the vault's shelves (or "empty" for a new vault). To feed the vault what they already
   know, they can run `/grimoire:train`.

Updating later: `claude plugin marketplace update grimoire && claude plugin update grimoire@grimoire`.
Removing: `claude plugin uninstall grimoire@grimoire`; the clone and personal memory are in
`~/.local/share/grimoire*` (`%LOCALAPPDATA%\grimoire*` on Windows).

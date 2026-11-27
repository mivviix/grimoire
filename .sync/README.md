# Auto-sync (Windows)

Any change in the folder is committed and pushed ~3 s after it stops; other devices' changes are pulled every 30 s.
Files over 5 MB stay on the device. If two devices edit the same file, both versions are kept:
the other device's keeps the name, this one's is saved as `name.conflict-<PC>-<time>.ext`.
Log: `.git\grimoire-sync.log`.

Claude sessions: open this folder with worktree off and stay on `main`; sync pauses on any other branch.

## Set up on another Windows device

1. Install Git (https://git-scm.com) and GitHub CLI (`winget install GitHub.cli`).
2. `gh auth login --web` (answer Yes to "Authenticate Git"), then `gh auth setup-git`.
3. `git config --global user.name "your name"` and `git config --global user.email "you@example.com"`.
4. `git clone https://github.com/mivviix/grimoire.git "$HOME\Documents\Vault"` (not in OneDrive/Dropbox).
5. `powershell -ExecutionPolicy Bypass -File "$HOME\Documents\Vault\.sync\install.ps1"`

Stop it: end the hidden `powershell.exe` running grimoire-sync.ps1 and delete the
`grimoire-sync Vault.lnk` shortcut from `shell:startup`.

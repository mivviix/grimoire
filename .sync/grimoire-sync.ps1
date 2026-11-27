# Keeps this git folder in sync with GitHub: commits+pushes local changes a few seconds
# after they stop, pulls remote changes every 30 s. Started hidden at login by install.ps1.
param([string]$Repo = (Split-Path $PSScriptRoot -Parent))

$ErrorActionPreference = 'Continue'
$env:GIT_TERMINAL_PROMPT = '0'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$Quiet = 3          # seconds of no changes before committing
$PullEvery = 30     # seconds between remote checks
$MaxBytes = 5MB     # bigger files stay on this device only

Set-Location $Repo
$gitDir = (git rev-parse --absolute-git-dir).Trim()
$log = Join-Path $gitDir 'grimoire-sync.log'
function Log($m) { "$(Get-Date -f s) $m" | Add-Content $log }

# one instance per folder
$mutex = New-Object Threading.Mutex($false, 'grimoire-sync-' + ($Repo.ToLower() -replace '[\\/:]', '_'))
if (-not $mutex.WaitOne(0)) { exit }

function Git { $out = & git @args 2>&1; if ($LASTEXITCODE) { Log "git $args -> $LASTEXITCODE $out" }; $out }

function Exclude-BigFiles {
    $exclude = Join-Path $gitDir 'info\exclude'
    $known = @(Get-Content $exclude -ErrorAction SilentlyContinue)
    $split = { param($s) ($s -join '') -split "`0" | Where-Object { $_ } }
    $tracked = @{}; & $split (git -c core.quotepath=off ls-files -z -m) | ForEach-Object { $tracked[$_] = 1 }
    $candidates = @($tracked.Keys) + @(& $split (git -c core.quotepath=off ls-files -z -o --exclude-standard))
    $candidates | Where-Object { $f = Get-Item -LiteralPath (Join-Path $Repo $_) -Force -ErrorAction SilentlyContinue; $f -and $f.Length -gt $MaxBytes } | ForEach-Object {
            $rel = $_
            if ($tracked[$rel]) {
                # ponytail: already-pushed file grew past 5 MB -> freeze it here instead of deleting it on other devices
                git update-index --skip-worktree -- $rel
            } else {
                $line = '/' + ($rel -replace '([\[\]\*\?!#])', '\$1')
                if ($known -notcontains $line) { Add-Content $exclude $line; $known += $line; Log "kept local (>5MB): $rel" }
            }
        }
}

function Merge-Remote {
    Git fetch --quiet origin | Out-Null
    if ($LASTEXITCODE) { return }
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    git merge --no-edit "origin/$branch" 2>&1 | Out-Null
    if (-not $LASTEXITCODE) { return }
    # conflict: remote version keeps the name, ours is saved next to it
    $stamp = Get-Date -f 'yyyyMMdd-HHmmss'
    foreach ($p in @(git diff --name-only --diff-filter=U)) {
        $stages = (git ls-files -u -- $p) -replace '^\S+ \S+ (\d).*', '$1'
        if ($stages -notcontains '3') { git add -- $p; continue }           # they deleted, we edited: keep ours
        if ($stages -contains '2') {
            git checkout --ours -- $p
            $dir = Split-Path $p; $name = [IO.Path]::GetFileNameWithoutExtension($p); $ext = [IO.Path]::GetExtension($p)
            $copy = "$name.conflict-$env:COMPUTERNAME-$stamp$ext"; if ($dir) { $copy = Join-Path $dir $copy }
            Copy-Item -LiteralPath $p -Destination $copy -Force
            git add -- $copy
            Log "conflict: $p -> kept both, ours in $copy"
        }
        git checkout --theirs -- $p; git add -- $p
    }
    Git commit --no-edit -m "sync: merge with conflicts kept from $env:COMPUTERNAME" | Out-Null
}

function Sync {
    if (Test-Path (Join-Path $gitDir 'MERGE_HEAD')) { git merge --abort 2>&1 | Out-Null }
    Exclude-BigFiles
    git add -A 2>&1 | Out-Null
    git diff --cached --quiet
    if ($LASTEXITCODE) { Git commit -q -m "sync: $env:COMPUTERNAME $(Get-Date -f 'yyyy-MM-dd HH:mm:ss')" | Out-Null }
    for ($i = 0; $i -lt 3; $i++) {
        Merge-Remote
        $ahead = git rev-list --count '@{u}..HEAD' 2>$null
        if (-not $ahead -or $ahead -eq '0') { return }
        Git push -q origin HEAD | Out-Null
        if (-not $LASTEXITCODE) { Log "pushed $ahead commit(s)"; return }
    }
}

$watcher = New-Object IO.FileSystemWatcher $Repo
$watcher.IncludeSubdirectories = $true
$watcher.InternalBufferSize = 65536
$global:lastChange = $null
foreach ($e in 'Changed', 'Created', 'Deleted', 'Renamed') {
    Register-ObjectEvent $watcher $e -Action {
        if ($Event.SourceEventArgs.FullPath -notmatch '\\\.git(\\|$)') { $global:lastChange = Get-Date }
    } | Out-Null
}
$watcher.EnableRaisingEvents = $true
Log "started in $Repo"

$lastPull = [datetime]::MinValue
while ($true) {
    $now = Get-Date
    if (($global:lastChange -and ($now - $global:lastChange).TotalSeconds -ge $Quiet) -or ($now - $lastPull).TotalSeconds -ge $PullEvery) {
        $global:lastChange = $null
        try { Sync } catch { Log "error: $_" }
        $lastPull = Get-Date
    }
    Start-Sleep -Milliseconds 500
}

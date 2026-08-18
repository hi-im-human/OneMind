<#
.SYNOPSIS
Agent Keep sync — stage everything not gitignored, optionally check identity-file
limits, commit, push. One command.

WHAT THIS DOES NOT DO: it does not scan for secrets. See SKILL.md. Exclusions are
your .gitignore's job, decided once, by a person.

.PARAMETER KeepRoot
Path to the agent's Keep (the git repo). Required, or set $env:AGENT_KEEP_ROOT.

.PARAMETER AgentName
Name used in the default commit message. Defaults to the Keep folder name.

.PARAMETER CheckScript
OPTIONAL path to an identity-file limit checker. If you do not set one, the step
is skipped. If you set one and the file is missing, this aborts rather than
continuing. A silent no-op can be mistaken for a passing check.

.PARAMETER Preview
Show what would be staged; change nothing.

.PARAMETER NoPush
Commit but do not push.

.PARAMETER Message
Custom one-liner commit message. Defaults to a timestamped checkpoint.
#>
param(
    [string]$KeepRoot    = $env:AGENT_KEEP_ROOT,
    [string]$AgentName   = "",
    [string]$CheckScript = $env:AGENT_LIMIT_CHECKER,
    [switch]$Preview,
    [switch]$NoPush,
    [string]$Message     = ""
)

function Write-H([string]$t) { Write-Host "`n-- $t" -ForegroundColor Cyan }

function Assert-Git([string]$what) {
    # Every git call is checked. Without this the script prints "Done." in green
    # after a FAILED push, which for a continuity tool is the worst possible lie:
    # you believe you have a checkpoint you do not have.
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n  $what FAILED (exit $LASTEXITCODE) -- stopping." -ForegroundColor Red
        Write-Host "  The Keep is NOT checkpointed. Fix the cause and re-run." -ForegroundColor Yellow
        exit 1
    }
}

if (-not $KeepRoot) {
    Write-Host "KeepRoot is required. Pass -KeepRoot '<path>' or set AGENT_KEEP_ROOT." -ForegroundColor Red
    exit 2
}
if (-not (Test-Path (Join-Path $KeepRoot ".git"))) {
    Write-Host "No .git found at $KeepRoot -- is that the repo root?" -ForegroundColor Red
    exit 2
}
if (-not $AgentName) { $AgentName = Split-Path $KeepRoot -Leaf }

# --- Status ----------------------------------------------------------------
Write-H "Keep status ($AgentName)"
$statusLines = git -C $KeepRoot status --short 2>&1
Assert-Git "git status"

if (-not $statusLines) {
    Write-Host "  Clean -- nothing to commit." -ForegroundColor Green
    if (-not $NoPush -and -not $Preview) {
        # Compare against the CURRENT branch's own upstream. Comparing against
        # origin/HEAD silently reports "nothing to do" in valid repo states where
        # origin/HEAD is missing or stale, leaving real commits unpushed.
        $branch = (git -C $KeepRoot rev-parse --abbrev-ref HEAD 2>&1)
        Assert-Git "git rev-parse"
        $upstream = (git -C $KeepRoot rev-parse --abbrev-ref "--symbolic-full-name" "@{u}" 2>$null)
        if ($LASTEXITCODE -ne 0 -or -not $upstream) {
            Write-Host "  No upstream set for '$branch' -- cannot tell if you are ahead." -ForegroundColor Yellow
            Write-Host "  Set one:  git -C `"$KeepRoot`" push -u origin $branch" -ForegroundColor Yellow
            exit 1
        }
        $ahead = [int](git -C $KeepRoot rev-list --count "$upstream..HEAD" 2>&1)
        Assert-Git "git rev-list"
        if ($ahead -gt 0) {
            Write-H "Pushing ($ahead commit(s) ahead of $upstream)"
            git -C $KeepRoot push 2>&1 | Write-Host
            Assert-Git "git push"
            Write-Host "  Pushed." -ForegroundColor Green
        } else {
            Write-Host "  Up to date with $upstream." -ForegroundColor Green
        }
    }
    exit 0
}
Write-Host ($statusLines | Out-String)

if ($Preview) {
    Write-H "Preview -- would stage:"
    $statusLines | ForEach-Object { Write-Host "  $_" }
    Write-Host "`nRun without -Preview to apply." -ForegroundColor Yellow
    exit 0
}

# --- Stage -----------------------------------------------------------------
Write-H "Staging all changes"
git -C $KeepRoot add -A 2>&1 | Write-Host
Assert-Git "git add -A"

# --- Optional identity-limit check -----------------------------------------
if ($CheckScript) {
    Write-H "Checking identity file limits"
    if (-not (Test-Path $CheckScript)) {
        Write-Host "  Checker configured but NOT FOUND at:" -ForegroundColor Red
        Write-Host "    $CheckScript" -ForegroundColor Red
        Write-Host "  Refusing to commit. Fix the path or unset AGENT_LIMIT_CHECKER." -ForegroundColor Yellow
        git -C $KeepRoot reset 2>&1 | Out-Null
        exit 1
    }
    python $CheckScript --keep $KeepRoot
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Identity check failed -- unstaging and aborting." -ForegroundColor Red
        git -C $KeepRoot reset 2>&1 | Out-Null
        exit 1
    }
    Write-Host "  Identity files within limits." -ForegroundColor Green
} else {
    Write-Host "  (No identity limit checker configured -- skipping.)" -ForegroundColor DarkGray
}

# --- Commit ----------------------------------------------------------------
Write-H "Committing"
if (-not $Message) {
    $Message = "sync: $AgentName Keep checkpoint $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}
git -C $KeepRoot commit -m $Message 2>&1 | Write-Host
Assert-Git "git commit"

# --- Push ------------------------------------------------------------------
if (-not $NoPush) {
    Write-H "Pushing"
    git -C $KeepRoot push 2>&1 | Write-Host
    Assert-Git "git push"
    Write-Host "  Pushed." -ForegroundColor Green
}

Write-H "Final status"
git -C $KeepRoot status --short 2>&1 | Write-Host

# Reached only if nothing above failed.
Write-Host "`nDone." -ForegroundColor Green

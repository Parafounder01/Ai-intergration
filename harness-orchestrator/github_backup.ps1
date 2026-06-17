<#
.SYNOPSIS
    GitHub Backup Script for Pavithra Harness Orchestrator

.DESCRIPTION
    Backs up test results, logs, and verification data to GitHub.
    Uses the `gh` CLI for authentication and git for commits.

    This script:
      1. Copies results to a timestamped backup directory
      2. Initializes git if needed (bare clone from Parafounder01/Ai-intergration)
      3. Commits with structured messages
      4. Pushes to remote

.PARAMETER RepoPath
    Path to the local repository or the harness-orchestrator project root

.PARAMETER ResultsDir
    Path to the results directory (e.g., work\results)

.PARAMETER Message
    Optional commit message override

.PARAMETER NoPush
    Only commit, don't push to remote

.EXAMPLE
    .\github_backup.ps1 -RepoPath "C:\Users\anant\OneDrive\Documents\opencode\harness-orchestrator"

    .\github_backup.ps1 -RepoPath "." -ResultsDir ".\work\results" -Message "Test run 2026-06-17"

.NOTES
    Requires: gh CLI (authenticated), git
    Repository: Parafounder01/Ai-intergration
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$RepoPath = ".",

    [Parameter(Mandatory = $false)]
    [string]$ResultsDir = "",

    [Parameter(Mandatory = $false)]
    [string]$Message = "",

    [switch]$NoPush
)

# ── CONFIGURATION ─────────────────────────────────────────────────
$ProjectRoot = Resolve-Path $RepoPath
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunLabel = "harness-run-$Timestamp"

if (-not $ResultsDir) {
    $ResultsDir = Join-Path $ProjectRoot "work\results"
}

$BackupRoot = Join-Path $ProjectRoot "github_backup"
$BackupDir = Join-Path $BackupRoot $RunLabel

$GitHubRepo = "Parafounder01/Ai-intergration"

# ── BANNER ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  GITHUB BACKUP — Pavithra Harness Orchestrator           ║" -ForegroundColor Cyan
Write-Host "║  Repository: $GitHubRepo" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── CHECK DEPENDENCIES ───────────────────────────────────────────
$PreCheckOk = $true

# Check git
try {
    $gitVersion = git --version 2>&1
    Write-Host "[OK] Git: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Git not found. Install from https://git-scm.com/" -ForegroundColor Red
    $PreCheckOk = $false
}

# Check gh CLI
try {
    $ghVersion = gh --version 2>&1 | Select-Object -First 1
    Write-Host "[OK] GitHub CLI: $ghVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] GitHub CLI not found. Install from https://cli.github.com/" -ForegroundColor Red
    $PreCheckOk = $false
}

# Check gh auth status
try {
    $ghAuth = gh auth status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] GitHub authenticated" -ForegroundColor Green
    } else {
        Write-Host "[WARN] GitHub not authenticated. Run: gh auth login" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] Could not check GitHub auth status" -ForegroundColor Yellow
}

if (-not $PreCheckOk) {
    Write-Host "`n[ERROR] Prerequisites missing. Aborting backup." -ForegroundColor Red
    exit 1
}

# ── COLLECT RESULTS ──────────────────────────────────────────────
Write-Host "`n>>> Collecting results from: $ResultsDir" -ForegroundColor Yellow

if (-not (Test-Path $ResultsDir)) {
    Write-Host "[WARN] Results directory not found: $ResultsDir" -ForegroundColor Yellow
    Write-Host "       Creating backup from work directory structure instead..."
    $ResultsDir = Join-Path $ProjectRoot "work"
    if (-not (Test-Path $ResultsDir)) {
        Write-Host "[ERROR] No work directory found. Nothing to back up." -ForegroundColor Red
        exit 1
    }
}

# Create backup directory
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# Copy results
if (Test-Path $ResultsDir) {
    Copy-Item -Path "$ResultsDir\*" -Destination $BackupDir -Recurse -Force
    Write-Host "[OK] Results copied to: $BackupDir" -ForegroundColor Green
}

# Also copy test reports
$TestReportPath = Join-Path $ProjectRoot "tests\TEST_REPORT.md"
if (Test-Path $TestReportPath) {
    Copy-Item -Path $TestReportPath -Destination $BackupDir -Force
    Write-Host "[OK] Test report copied" -ForegroundColor Green
}

$TestReportJson = Join-Path $ProjectRoot "tests\TEST_REPORT.json"
if (Test-Path $TestReportJson) {
    Copy-Item -Path $TestReportJson -Destination $BackupDir -Force
}

# Copy logs
$LogDir = Join-Path $ProjectRoot "work\logs"
if (Test-Path $LogDir) {
    $LogBackupDir = Join-Path $BackupDir "logs"
    New-Item -ItemType Directory -Force -Path $LogBackupDir | Out-Null
    Copy-Item -Path "$LogDir\*" -Destination $LogBackupDir -Force
    Write-Host "[OK] Logs copied" -ForegroundColor Green
}

# ── CREATE BACKUP MANIFEST ──────────────────────────────────────
$Manifest = @{
    BackupDate      = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    RunLabel        = $RunLabel
    GitHubRepo      = $GitHubRepo
    FilesBackedUp   = @()
    ResultsCount    = (Get-ChildItem -Recurse -File $BackupDir).Count
}

# List files in backup
$Manifest.FilesBackedUp = Get-ChildItem -Recurse -File $BackupDir | ForEach-Object {
    $_.FullName.Replace($BackupDir, "").TrimStart("\")
}

$ManifestPath = Join-Path $BackupDir "BACKUP_MANIFEST.json"
$Manifest | ConvertTo-Json -Depth 3 | Out-File -FilePath $ManifestPath -Encoding UTF8
Write-Host "[OK] Backup manifest created" -ForegroundColor Green

# ── GIT OPERATIONS ───────────────────────────────────────────────
Write-Host "`n>>> Preparing Git commit..." -ForegroundColor Yellow

# Try to find or clone the Ai-intergration repo
$GitCloneDir = Join-Path $ProjectRoot "..\Ai-intergration"
$GitCloneDir = Resolve-Path $GitCloneDir -ErrorAction SilentlyContinue

if (-not $GitCloneDir) {
    # Try common locations
    $PossibleLocations = @(
        Join-Path $ProjectRoot "..\Ai-intergration"
        Join-Path $ProjectRoot "..\..\Ai-intergration"
        "C:\Users\anant\OneDrive\Documents\opencode\Ai-intergration"
    )
    
    foreach ($loc in $PossibleLocations) {
        $resolved = Resolve-Path $loc -ErrorAction SilentlyContinue
        if ($resolved) {
            $GitCloneDir = $resolved
            break
        }
    }
}

if (-not $GitCloneDir) {
    Write-Host "[WARN] Could not find Ai-intergration repository locally." -ForegroundColor Yellow
    Write-Host "       Attempting to clone from GitHub..."
    
    $CloneTarget = Join-Path $ProjectRoot "repos\Ai-intergration"
    New-Item -ItemType Directory -Force -Path (Split-Path $CloneTarget -Parent) | Out-Null
    
    try {
        gh repo clone Parafounder01/Ai-intergration $CloneTarget -- --depth 1
        if ($LASTEXITCODE -eq 0) {
            $GitCloneDir = $CloneTarget
            Write-Host "[OK] Cloned to: $GitCloneDir" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] Failed to clone repository" -ForegroundColor Red
        }
    } catch {
        Write-Host "[FAIL] Clone failed: $_" -ForegroundColor Red
    }
}

if ($GitCloneDir -and (Test-Path $GitCloneDir)) {
    Push-Location $GitCloneDir
    
    try {
        # Copy backup into the repo
        $RepoBackupDir = Join-Path $GitCloneDir "harness-orchestrator-backups"
        New-Item -ItemType Directory -Force -Path $RepoBackupDir | Out-Null
        
        $RunBackupDir = Join-Path $RepoBackupDir $RunLabel
        Copy-Item -Path "$BackupDir\*" -Destination $RunBackupDir -Recurse -Force
        
        # Also copy the full harness-orchestrator project
        $HarnessTarget = Join-Path $GitCloneDir "harness-orchestrator"
        if (-not (Test-Path $HarnessTarget)) {
            # Copy only key files, not the entire work dir
            $ExcludeDirs = @("work\inputs", "work\outputs", "work\results", "work\logs", "__pycache__")
            Copy-Item -Path "$ProjectRoot\*.py" -Destination $HarnessTarget -Force
            Copy-Item -Path "$ProjectRoot\*.ps1" -Destination $HarnessTarget -Force
            Copy-Item -Path "$ProjectRoot\*.sh" -Destination $HarnessTarget -Force
            Copy-Item -Path "$ProjectRoot\*.md" -Destination $HarnessTarget -Force
            Copy-Item -Path "$ProjectRoot\.github" -Destination $HarnessTarget -Recurse -Force
            
            # Copy architecture docs
            if (Test-Path (Join-Path $ProjectRoot "architecture.md")) {
                Copy-Item (Join-Path $ProjectRoot "architecture.md") -Destination $HarnessTarget -Force
            }
            
            Write-Host "[OK] Harness orchestrator code copied to repo" -ForegroundColor Green
        }
        
        # Git operations
        git add -A
        
        $CommitMsg = if ($Message) { $Message } else { "chore(harness): backup harness-orchestrator run $RunLabel" }
        
        git commit -m $CommitMsg -m "Auto-backup from Pavithra Harness Orchestrator" -m "- Run label: $RunLabel" -m "- Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Committed: $CommitMsg" -ForegroundColor Green
            
            if (-not $NoPush) {
                Write-Host ">>> Pushing to GitHub..." -ForegroundColor Yellow
                try {
                    git push origin main 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "[OK] Pushed to GitHub: $GitHubRepo" -ForegroundColor Green
                    } else {
                        # Try with different branch
                        git branch -M main
                        git push -u origin main 2>&1
                        if ($LASTEXITCODE -eq 0) {
                            Write-Host "[OK] Pushed to GitHub (new branch main)" -ForegroundColor Green
                        } else {
                            Write-Host "[WARN] Push failed. You may need to set upstream branch." -ForegroundColor Yellow
                            Write-Host "       Try: git push -u origin main" -ForegroundColor Yellow
                        }
                    }
                } catch {
                    Write-Host "[WARN] Push failed: $_" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "[INFO] Nothing new to commit (no changes)" -ForegroundColor Green
        }
        
    } finally {
        Pop-Location
    }
}

# ── SUMMARY ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  BACKUP COMPLETE                                          ║" -ForegroundColor Cyan
Write-Host "╠═══════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  Run Label:     $RunLabel" -ForegroundColor Cyan
Write-Host "║  Backup Path:   $BackupDir" -ForegroundColor Cyan
if ($GitCloneDir) {
    Write-Host "║  Git Repo:      $GitCloneDir" -ForegroundColor Cyan
    Write-Host "║  Remote:        https://github.com/$GitHubRepo" -ForegroundColor Cyan
}
Write-Host "║  Files Backed Up: $($Manifest.ResultsCount)" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Return the backup path
return $BackupDir

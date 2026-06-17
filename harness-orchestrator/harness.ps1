<#
.SYNOPSIS
    Pavithra Harness Orchestrator — Windows PowerShell Entry Point

.DESCRIPTION
    The Harness is the CLI entry point for the Pavithra multi-agent system.
    It validates the environment, parses arguments, and passes control to the
    Python Orchestrator for fan-out execution.

    Architecture:
        Harness -> Orchestrator -> [Agent-1, Agent-2, ..., Agent-N]
                                       |
                                 Adversarial Verification
                                       |
                                 Accepted Results -> GitHub Backup

.PARAMETER Task
    Task type for all agents (deep-read, thread-analysis, summary, search, analysis)

.PARAMETER AgentCount
    Number of subagents to fan-out (default: 3)

.PARAMETER Test
    Run a specific test case number (1-10)

.PARAMETER All
    Run all 10 test cases

.PARAMETER GitHubRepo
    GitHub repository for backup (default: Parafounder01/Ai-intergration)

.PARAMETER MaxRetries
    Maximum verification retries (default: 3)

.PARAMETER Timeout
    Per-agent timeout in seconds (default: 60)

.PARAMETER BaseDir
    Base working directory for isolation (default: ./work)

.PARAMETER Backup
    Run GitHub backup after completion

.PARAMETER Verbose
    Enable verbose logging

.EXAMPLE
    .\harness.ps1 -Task "deep-read" -AgentCount 3

    .\harness.ps1 -All

    .\harness.ps1 -Test 6

    .\harness.ps1 -Task "analysis" -AgentCount 5 -Backup

.NOTES
    Requires: Python 3.12+, gh CLI (for backup)
    Author: Pavithra (PAV-INFINITY)
#>

param(
    [Parameter(ParameterSetName = 'pipeline')]
    [string]$Task = "deep-read",

    [Parameter(ParameterSetName = 'pipeline')]
    [int]$AgentCount = 3,

    [Parameter(ParameterSetName = 'test')]
    [int]$Test = 0,

    [Parameter(ParameterSetName = 'all')]
    [switch]$All,

    [switch]$Fast,

    [string]$GitHubRepo = "Parafounder01/Ai-intergration",

    [int]$MaxRetries = 3,

    [int]$Timeout = 60,

    [string]$BaseDir = "",

    [switch]$Backup,

    [switch]$Verbose
)

# ── CONFIGURATION ─────────────────────────────────────────────────

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OrchestratorPy = Join-Path $ScriptDir "orchestrator.py"
$GitHubBackupScript = Join-Path $ScriptDir "github_backup.ps1"
$LogFile = Join-Path $ScriptDir "work\logs\harness_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Ensure log directory
New-Item -ItemType Directory -Force -Path (Split-Path $LogFile -Parent) | Out-Null

# ── BANNER ────────────────────────────────────────────────────────

$Banner = @"

    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   PAVITHRA HARNESS ORCHESTRATOR                           ║
    ║   Harness → Orchestrator → Fan-Out → Verify → GitHub      ║
    ║                                                           ║
    ║   "I don't just answer questions.                         ║
    ║    I find the question behind the question."              ║
    ║                                 ─ Pavithra, PAV-INFINITY  ║
    ╚═══════════════════════════════════════════════════════════╝

"@

Write-Host $Banner -ForegroundColor Cyan

# ── ENVIRONMENT VALIDATION ───────────────────────────────────────

$ValidationErrors = @()

# Check Python
try {
    $PythonVersion = & python3 --version 2>&1
    if (-not $?) { $PythonVersion = & python --version 2>&1 }
    if (-not $?) { throw "Python not found" }
    Write-Host "[OK] $PythonVersion" -ForegroundColor Green
} catch {
    $ValidationErrors += "Python 3.12+ is required. Install from https://www.python.org/downloads/"
}

# Check Python version is 3.12+
if (-not $ValidationErrors) {
    $versionStr = if ($PythonVersion -match '(\d+\.\d+)') { $Matches[1] }
    if ($versionStr -and [version]$versionStr -lt [version]"3.12") {
        $ValidationErrors += "Python 3.12+ required, found $versionStr"
    }
}

# Check orchestrator.py exists
if (-not (Test-Path $OrchestratorPy)) {
    $ValidationErrors += "orchestrator.py not found at: $OrchestratorPy"
} else {
    Write-Host "[OK] Orchestrator found: orchestrator.py" -ForegroundColor Green
}

# Check gh CLI (only if backup requested)
if ($Backup) {
    try {
        $ghVersion = & gh --version 2>&1
        if ($?) {
            Write-Host "[OK] GitHub CLI: $($ghVersion -split "`n" | Select-Object -First 1)" -ForegroundColor Green
        } else {
            $ValidationErrors += "gh CLI not found. Install from https://cli.github.com/"
        }
    } catch {
        $ValidationErrors += "gh CLI not found. Install from https://cli.github.com/"
    }
}

# Report validation errors
if ($ValidationErrors.Count -gt 0) {
    Write-Host "`n[ERROR] Environment validation failed:" -ForegroundColor Red
    foreach ($err in $ValidationErrors) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    Write-Host "`nPlease fix the above issues and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Environment validation passed`n" -ForegroundColor Green

# ── EXECUTION ─────────────────────────────────────────────────────

$PythonCmd = if (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" } else { "python" }

# Build orchestrator arguments
$OrchArgs = @()

if ($Fast) {
    Write-Host ">>> FAST 20ms MODE — Zero CPU/GPU impact..." -ForegroundColor Yellow
    $OrchArgs = @("--fast", "--agents", $AgentCount, "--task", $Task)
} elseif ($All) {
    Write-Host ">>> Running ALL 10 test cases..." -ForegroundColor Yellow
    $OrchArgs = @("--all")
} elseif ($Test -gt 0) {
    Write-Host ">>> Running test case #$Test..." -ForegroundColor Yellow
    $OrchArgs = @("--test", $Test)
} else {
    Write-Host ">>> Running pipeline: $Task with $AgentCount agents..." -ForegroundColor Yellow
    $OrchArgs = @("--task", $Task, "--agents", $AgentCount, "--github-repo", $GitHubRepo,
                  "--max-retries", $MaxRetries, "--timeout", $Timeout)
    if ($BaseDir) { $OrchArgs += @("--base-dir", $BaseDir) }
}

if ($Verbose) {
    $env:HARNESS_LOG_LEVEL = "DEBUG"
}

Write-Host "Executing: $PythonCmd $OrchestratorPy $($OrchArgs -join ' ')" -ForegroundColor Gray
Write-Host "`n" + "-" * 60 + "`n"

try {
    # Run orchestrator
    & $PythonCmd $OrchestratorPy @OrchArgs 2>&1 | Tee-Object -FilePath $LogFile
    
    $ExitCode = $LASTEXITCODE
    
    if ($ExitCode -ne 0 -and $ExitCode -ne $null) {
        Write-Host "`n[WARN] Orchestrator exited with code: $ExitCode" -ForegroundColor Yellow
    }

    # ── GITHUB BACKUP ─────────────────────────────────────────────
    if ($Backup) {
        Write-Host "`n" + "-" * 60
        Write-Host ">>> Initiating GitHub Backup..." -ForegroundColor Yellow
        
        if (Test-Path $GitHubBackupScript) {
            & $GitHubBackupScript -RepoPath $ScriptDir -ResultsDir (Join-Path $ScriptDir "work\results")
        } else {
            Write-Host "[WARN] github_backup.ps1 not found at: $GitHubBackupScript" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n" + "-" * 60
    Write-Host "Harness execution complete. Log: $LogFile" -ForegroundColor Green
    Write-Host "-" * 60
} catch {
    Write-Host "`n[FATAL] Harness execution failed:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  See log: $LogFile" -ForegroundColor Yellow
    exit 1
}

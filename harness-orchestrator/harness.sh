#!/usr/bin/env bash
# ==============================================================================
# Pavithra Harness Orchestrator — Linux Bash Entry Point
#
# Architecture:
#   Harness -> Orchestrator -> [Agent-1, Agent-2, ..., Agent-N]
#                                  |
#                            Adversarial Verification
#                                  |
#                            Accepted Results -> GitHub Backup
#
# Usage:
#   ./harness.sh --task "deep-read" --agents 3
#   ./harness.sh --all
#   ./harness.sh --test 6
#   ./harness.sh --task "analysis" --agents 5 --backup
#
# Requires: Python 3.12+, gh CLI (for backup)
# Author: Pavithra (PAV-INFINITY)
# ==============================================================================

set -euo pipefail

# ── CONFIGURATION ─────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRATOR_PY="${SCRIPT_DIR}/orchestrator.py"
GITHUB_BACKUP_SCRIPT="${SCRIPT_DIR}/github_backup.ps1"
LOG_DIR="${SCRIPT_DIR}/work/logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/harness_$(date +%Y%m%d_%H%M%S).log"

# ── BANNER ────────────────────────────────────────────────────────
cat << 'EOF'

    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   PAVITHRA HARNESS ORCHESTRATOR                           ║
    ║   Harness → Orchestrator → Fan-Out → Verify → GitHub      ║
    ║                                                           ║
    ║   "I don't just answer questions.                         ║
    ║    I find the question behind the question."              ║
    ║                                 ─ Pavithra, PAV-INFINITY  ║
    ╚═══════════════════════════════════════════════════════════╝

EOF

# ── PARSE ARGUMENTS ──────────────────────────────────────────────
TASK="deep-read"
AGENT_COUNT=3
TEST=0
ALL=false
GITHUB_REPO="Parafounder01/Ai-intergration"
MAX_RETRIES=3
TIMEOUT=60
BASE_DIR=""
FAST=false
BACKUP=false
VERBOSE=false

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
  --task <type>         Task type (deep-read, thread-analysis, summary, search, analysis)
  --agents <count>      Number of subagents (default: 3)
  --test <number>       Run a specific test case (1-10)
  --all                 Run all 10 test cases
  --github-repo <repo>  GitHub repository for backup (default: Parafounder01/Ai-intergration)
  --max-retries <n>     Max verification retries (default: 3)
  --timeout <seconds>   Per-agent timeout (default: 60)
  --base-dir <path>     Base working directory for isolation
  --fast                Fast 20ms mode (zero CPU/GPU impact)
  --backup              Run GitHub backup after completion
  --verbose             Enable verbose logging
  --help                Show this help message

Examples:
  $0 --task "deep-read" --agents 3
  $0 --all
  $0 --test 6
  $0 --task "analysis" --agents 5 --backup
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --task)           TASK="$2"; shift 2 ;;
        --agents)         AGENT_COUNT="$2"; shift 2 ;;
        --test)           TEST="$2"; shift 2 ;;
        --all)            ALL=true; shift ;;
        --github-repo)    GITHUB_REPO="$2"; shift 2 ;;
        --max-retries)    MAX_RETRIES="$2"; shift 2 ;;
        --timeout)        TIMEOUT="$2"; shift 2 ;;
        --base-dir)       BASE_DIR="$2"; shift 2 ;;
        --fast)           FAST=true; shift ;;
        --backup)         BACKUP=true; shift ;;
        --verbose)        VERBOSE=true; shift ;;
        --help)           usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# ── ENVIRONMENT VALIDATION ───────────────────────────────────────
VALIDATION_ERRORS=()

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    echo -e "\e[32m[OK]\e[0m Python3 found: $(python3 --version)"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
    echo -e "\e[32m[OK]\e[0m Python found: $(python --version)"
else
    VALIDATION_ERRORS+=("Python 3.12+ is required. Install from https://www.python.org/downloads/")
fi

# Check orchestrator.py exists
if [[ ! -f "$ORCHESTRATOR_PY" ]]; then
    VALIDATION_ERRORS+=("orchestrator.py not found at: $ORCHESTRATOR_PY")
else
    echo -e "\e[32m[OK]\e[0m Orchestrator found: orchestrator.py"
fi

# Check gh CLI (only if backup requested)
if [[ "$BACKUP" == true ]]; then
    if command -v gh &>/dev/null; then
        echo -e "\e[32m[OK]\e[0m GitHub CLI: $(gh --version | head -1)"
    else
        VALIDATION_ERRORS+=("gh CLI not found. Install from https://cli.github.com/")
    fi
fi

# Report validation errors
if [[ ${#VALIDATION_ERRORS[@]} -gt 0 ]]; then
    echo -e "\n\e[31m[ERROR] Environment validation failed:\e[0m"
    for err in "${VALIDATION_ERRORS[@]}"; do
        echo -e "  \e[31m- $err\e[0m"
    done
    echo -e "\e[33mPlease fix the above issues and try again.\e[0m"
    exit 1
fi

echo -e "\e[32m[OK] Environment validation passed\e[0m\n"

# ── EXECUTION ─────────────────────────────────────────────────────
ORCH_ARGS=()

if [[ "$FAST" == true ]]; then
    echo -e "\e[33m>>> FAST 20ms MODE (zero CPU/GPU impact)...\e[0m"
    ORCH_ARGS+=("--fast" "--agents" "$AGENT_COUNT" "--task" "$TASK")
elif [[ "$ALL" == true ]]; then
    echo -e "\e[33m>>> Running ALL 10 test cases...\e[0m"
    ORCH_ARGS+=("--all")
elif [[ "$TEST" -gt 0 ]]; then
    echo -e "\e[33m>>> Running test case #${TEST}...\e[0m"
    ORCH_ARGS+=("--test" "$TEST")
else
    echo -e "\e[33m>>> Running pipeline: ${TASK} with ${AGENT_COUNT} agents...\e[0m"
    ORCH_ARGS+=("--task" "$TASK" "--agents" "$AGENT_COUNT" "--github-repo" "$GITHUB_REPO")
    ORCH_ARGS+=("--max-retries" "$MAX_RETRIES" "--timeout" "$TIMEOUT")
    if [[ -n "$BASE_DIR" ]]; then
        ORCH_ARGS+=("--base-dir" "$BASE_DIR")
    fi
fi

if [[ "$VERBOSE" == true ]]; then
    export HARNESS_LOG_LEVEL="DEBUG"
fi

echo "Executing: $PYTHON_CMD $ORCHESTRATOR_PY ${ORCH_ARGS[*]}"
echo ""
echo "------------------------------------------------------------"
echo ""

# Run orchestrator
set +e
if [[ "$VERBOSE" == true ]]; then
    $PYTHON_CMD "$ORCHESTRATOR_PY" "${ORCH_ARGS[@]}" 2>&1 | tee "$LOG_FILE"
else
    $PYTHON_CMD "$ORCHESTRATOR_PY" "${ORCH_ARGS[@]}" >> "$LOG_FILE" 2>&1
    # Show last few lines from log
    echo "Execution logged to: $LOG_FILE"
    echo ""
    echo "--- Last 20 lines of output ---"
    tail -20 "$LOG_FILE"
fi
EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -ne 0 ]]; then
    echo -e "\n\e[33m[WARN] Orchestrator exited with code: $EXIT_CODE\e[0m"
fi

# ── GITHUB BACKUP ────────────────────────────────────────────────
if [[ "$BACKUP" == true ]]; then
    echo ""
    echo "------------------------------------------------------------"
    echo -e "\e[33m>>> Initiating GitHub Backup...\e[0m"
    
    if [[ -f "$GITHUB_BACKUP_SCRIPT" ]]; then
        # We call the PowerShell script via pwsh if available, otherwise note the limitation
        if command -v pwsh &>/dev/null; then
            pwsh -File "$GITHUB_BACKUP_SCRIPT" -RepoPath "$SCRIPT_DIR" -ResultsDir "${SCRIPT_DIR}/work/results"
        else
            echo -e "\e[33mPowerShell not available. Manual backup: cd $SCRIPT_DIR && ./github_backup.ps1\e[0m"
        fi
    else
        echo -e "\e[33m[WARN] github_backup.ps1 not found\e[0m"
    fi
fi

echo ""
echo "------------------------------------------------------------"
echo -e "\e[32mHarness execution complete. Log: $LOG_FILE\e[0m"
echo "------------------------------------------------------------"

exit $EXIT_CODE

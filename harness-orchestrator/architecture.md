# 🏗️ Pavithra Harness → Orchestrator → Fan-Out Architecture

## Architecture Overview

```
User Request
     │
     ▼
┌─────────────────────────────────────────────┐
│  HARNESS (Entry Point / CLI / Trigger)       │
│  - Accepts input                             │
│  - Validates parameters                      │
│  - Passes to Orchestrator                    │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  ORCHESTRATOR (Master Controller)            │
│  - Fan-Out: spawns N subagent tasks          │
│  - Assigns each subagent ONE isolated task   │
│  - Enforces 3 core rules:                    │
│    1) DETERMINE     → Analyze what to do     │
│    2) CONTENT ISOLATION → No cross-talk      │
│    3) ADVERSARIAL VERIFICATION → Cross-check │
│  - Collects results                          │
│  - Runs 10 test cases total                  │
│  - Backs up to GitHub                        │
└──────┬──────┬──────┬──────┬──────┬──────────┘
       │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼
    ┌─────────────────────────────────┐
    │  FAN-OUT: N Pavithra Subagents  │
    │  @pavithragent-1  → Task 1      │
    │  @pavithragent-2  → Task 2      │
    │  @pavithragent-3  → Task 3      │
    │  ...                             │
    │  @pavithragent-N  → Task N      │
    │  (Each: isolated, determined,   │
    │   adversary-verified result)    │
    └─────────────────────────────────┘
```

## The 3 Core Rules

### Rule 1: DETERMINE
Each subagent must first analyze its assigned task and determine:
- What is the exact task scope?
- What data does it need?
- What tools/methods will it use?
- What is the expected output format?
- Document this as a `DETERMINATION.md` per subagent

### Rule 2: CONTENT ISOLATION
- Each subagent runs in its own sandboxed context/directory
- Subagent-N cannot see Subagent-M's files or outputs
- Each agent has its own:
  - Working directory: `work/outputs/agent-N/`
  - Input manifest: `work/inputs/agent-N/`
  - Results: `work/results/agent-N/`
- No cross-agent file reads or variable sharing
- Only the Orchestrator can read all outputs after completion

### Rule 3: ADVERSARIAL VERIFICATION
After each subagent produces output, an adversary subagent cross-checks it:
- Subagent-A produces result → Subagent-B (adversary) verifies
- Verifier checks: accuracy, completeness, consistency, security
- If verifier flags issues → result is REJECTED → original agent re-runs
- If verifier passes → result is ACCEPTED
- Only accepted results go into final output

## Data Flow

```
1. HARNESS receives request
   │
2. HARNESS validates and forwards to ORCHESTRATOR
   │
3. ORCHESTRATOR decomposes task into N subtasks
   │
4. For each subtask i:
   ├── Create isolation bubble (work/inputs/agent-i/, work/outputs/agent-i/)
   ├── Subagent-i runs DETERMINE phase
   ├── Subagent-i executes task
   ├── Subagent-i writes result to work/outputs/agent-i/
   │
5. ORCHESTRATOR runs ADVERSARIAL VERIFICATION:
   ├── Assign verifier j = (i+1) % N
   ├── Verifier checks output_i
   ├── If PASS → copy to work/results/agent-i/
   ├── If FAIL → reject, notify, retry
   │
6. ORCHESTRATOR collects all accepted results
   │
7. Results backed up to GitHub (if configured)
   │
8. Final report generated
```

## System Components

| Component | File | Language | Role |
|-----------|------|----------|------|
| Harness | `harness.ps1` | PowerShell | Windows entry point |
| Harness | `harness.sh` | Bash | Linux entry point |
| Orchestrator | `orchestrator.py` | Python | Master controller |
| Agent Template | `agent_template.py` | Python | Base subagent class |
| Adversary | `adversary.py` | Python | Verification engine |
| Isolation Manager | `isolation_manager.py` | Python | Sandbox/fence per agent |
| Test Runner | `test_runner.py` | Python | 10-test-case executor |
| GitHub Backup | `github_backup.ps1` | PowerShell | GitHub sync |
| CI Pipeline | `.github/workflows/harness-ci.yml` | YAML | GitHub Actions |

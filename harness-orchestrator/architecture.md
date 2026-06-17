# 🏗️ @pavithragent Multi-Agent Fan-Out Architecture

## Architecture Overview

```
@pavithragent (Main Orchestrator)
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (Master Controller)                            │
│  - Fan-Out: spawns N subagent tasks                          │
│  - Assigns each subagent ONE isolated task                   │
│  - Enforces 3 core rules:                                    │
│    1) DETERMINE     → Analyze what to do                     │
│    2) CONTENT ISOLATION → No cross-talk                      │
│    3) ADVERSARIAL VERIFICATION → Cross-check                 │
│  - Collects results                                          │
│  - Runs conclusion aggregation                               │
│  - Backs up to GitHub                                        │
└──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┘
       │      │      │      │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌──────────────────────────────────────────────────────────────────┐
│  FAN-OUT: Specialized Subagents (10 total)                       │
│                                                                  │
│  @pavithragent_1  → Deep-Read Specialist     (task 1)            │
│  @pavithragent_2  → Thread-Analysis Specialist (task 2)          │
│  @pavithragent_3  → Summary Specialist        (task 3)           │
│  @pavithragent_4  → Search Specialist         (task 4)           │
│  @pavithragent_5  → Analysis Specialist       (task 5)           │
│  @pavithragent_6  → Verification / Adversary   (task 6)          │
│  @pavithragent_7  → Security-Audit Specialist  (task 7)          │
│  @pavithragent_8  → Cross-Reference Specialist (task 8)          │
│  @pavithragent_9  → Error-Recovery Specialist  (task 9)          │
│  @pavithragent_10 → Conclusion Aggregator      (task 10)         │
│                                                                  │
│  (Each: isolated, determined, adversary-verified)                │
└──────────────────────────────────────────────────────────────────┘
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
- 5 checks: schema, isolation, consistency, completeness, security
- If verifier flags issues → result is REJECTED → original agent re-runs
- If verifier passes → result is ACCEPTED
- Only accepted results go into final output

## Data Flow

```
1. @pavithragent (main) receives request
   │
2. ORCHESTRATOR decomposes into up to 10 specialized subtasks
   │
3. For each subtask i (1-10):
   ├── Create isolation bubble (work/inputs/agent-i/, work/outputs/agent-i/)
   ├── @pavithragent_i runs DETERMINE phase
   ├── @pavithragent_i executes task
   ├── @pavithragent_i writes result to work/outputs/agent-i/
   │
4. ORCHESTRATOR runs ADVERSARIAL VERIFICATION (round-robin):
   ├── Assign verifier j = (i+1) % N
   ├── Verifier checks output_i (5 checks)
   ├── If PASS → copy to work/results/agent-i/
   ├── If FAIL → reject, notify, retry (up to 3x)
   │
5. ORCHESTRATOR collects all accepted results
   │
6. @pavithragent_10 (Conclusion) aggregates all outputs:
   ├── Builds summary_by_agent
   ├── Generates cross_agent_insights
   ├── Produces final_verdict (PASS / PARTIAL / FAIL)
   ├── Lists recommendations
   │
7. Results backed up to GitHub
   │
8. Final report generated
```

## Comparison: Before vs After

| Aspect | Before (Old) | After (New) |
|--------|-------------|-------------|
| Entry point | `harness.ps1` + `harness.sh` | `orchestrator.py` (direct) |
| Harness.ps1 | Existed (broken -Backup flag) | **REMOVED** |
| Architecture | Harness → Orchestrator → Fan-Out | @pavithragent → 10 specialized subagents |
| Agent identity | Generic agent-1..N | Named: @pavithragent_1 through _10 |
| Task specialization | All agents same type | Each agent has unique role |
| Conclusion | No aggregation | @pavithragent_10 aggregates all |
| Fast 20ms mode | Available | Available (unchanged) |

## System Components

| Component | File | Language | Role |
|-----------|------|----------|------|
| Orchestrator | `orchestrator.py` | Python | Master controller (@pavithragent main) |
| Agent Template | `agent_template.py` | Python | Base subagent class |
| Adversary | `adversary.py` | Python | Verification engine (5 checks) |
| Isolation Manager | `isolation_manager.py` | Python | Sandbox/fence per agent |
| Test Runner | `test_runner.py` | Python | 10-test-case executor |
| GitHub Backup | `github_backup.ps1` | PowerShell | GitHub sync |
| CI Pipeline | `.github/workflows/harness-ci.yml` | YAML | GitHub Actions |
| Agent defs (1-10) | `~/.config/opencode/agents/pavithragent_*.md` | Markdown | Subagent role definitions |
| Entry (Win) | `python orchestrator.py --orchestrate "prompt"` | CLI | Windows direct |
| Entry (Linux) | `python3 orchestrator.py --orchestrate "prompt"` | CLI | Linux direct |

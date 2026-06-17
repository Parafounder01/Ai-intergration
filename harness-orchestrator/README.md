# Pavithra Harness Orchestrator

## Overview

The **Pavithra Harness Orchestrator** is a multi-agent system architecture that implements a **Harness Orchestrator Fan-Out** pattern. It spawns N-number of @pavithragent subagents, each handling one isolated task, runs them through adversarial verification, and backs up results to GitHub.

```
User
 |
 v
+-----------------------+
|      HARNESS           |  CLI entry point (PowerShell / Bash)
+-----------------------+
         |
         v
+-----------------------+
|    ORCHESTRATOR        |  Master controller (Python)
+-----------------------+
    /    |    |    \
   v     v    v    v
+----+ +----+ +----+ +----+
|A1  | |A2  | |A3  | |AN  |  N subagents (isolated)
+----+ +----+ +----+ +----+
   |     |     |     |
   +---> ADVERSARIAL VERIFICATION <---+
         |
         v
+-----------------------+
| ACCEPTED RESULTS       |
+-----------------------+
         |
         v
+-----------------------+
| GITHUB BACKUP          |
+-----------------------+
```

## The 3 Rules

### 1. DETERMINE
Each subagent first analyzes its task — scoping what needs to be done, what data is needed, and what tools to use. This determination is documented per agent.

### 2. CONTENT ISOLATION
Each subagent runs in its own sandboxed directory. Agent-1 cannot see Agent-2's files. Only the Orchestrator reads across isolation boundaries after all agents complete.

### 3. ADVERSARIAL VERIFICATION
Every subagent output is cross-checked by another subagent (adversary). The verifier checks for accuracy, completeness, consistency, and security. Failed outputs trigger a retry.

## Quick Start

### Prerequisites
- Python 3.12+
- PowerShell 5.1+ (Windows) or Bash (Linux)
- `gh` CLI (for GitHub backup)

### Clone the Repo
```bash
gh repo clone Parafounder01/Ai-intergration
cd Ai-intergration
```

### Run the Harness (Windows)
```powershell
.\harness.ps1 -Task "deep-read C:\path\to\files" -AgentCount 3
```

### Run the Harness (Linux)
```bash
./harness.sh --task "deep-read /path/to/files" --agents 3
```

### Run All 10 Test Cases
```bash
python test_runner.py --all
```

### Run a Specific Test
```bash
python test_runner.py --test 1
```

### Run with Custom Agent Count
```bash
python orchestrator.py --task "analyze" --agents 5
```

## Architecture

Detailed architecture documentation is in `architecture.md`.

### File Structure
```
harness-orchestrator/
├── README.md                  # This file
├── architecture.md            # Detailed architecture
├── harness.ps1                # Windows entry point
├── harness.sh                 # Linux entry point
├── orchestrator.py            # Master controller
├── agent_template.py          # Base subagent class
├── adversary.py               # Verification engine
├── isolation_manager.py       # Sandbox per agent
├── test_runner.py             # 10-test-case executor
├── github_backup.ps1          # GitHub push script
├── work/
│   ├── inputs/agent-N/        # Per-agent input manifests
│   ├── outputs/agent-N/       # Per-agent working directories
│   ├── results/agent-N/       # Accepted results
│   └── logs/                  # Orchestrator logs
├── tests/
│   ├── test_01_single_agent/
│   ├── test_02_dual_agent/
│   ├── ... (10 total)
└── .github/workflows/
    └── harness-ci.yml         # GitHub Actions
```

## 10 Test Cases

| Test | Name | Description | Expected Outcome |
|------|------|-------------|-----------------|
| 1 | Single Agent | 1 subagent, simple deep-read task | Agent produces valid output |
| 2 | Dual Agent | 2 subagents, independent files | Both agents produce valid isolated output |
| 3 | Triple Agent | 3 subagents, different tasks | All 3 produce valid output |
| 4 | Adversary Pass | Subagent output passes verification | Verification returns PASS |
| 5 | Adversary Reject | Subagent output fails first, retries, passes | Verification initially REJECTS, then PASSES |
| 6 | Content Isolation | Agent1 tries to access Agent2's data | Access blocked, isolation confirmed |
| 7 | Large Fan-Out | 5 subagents in parallel | All 5 produce valid output |
| 8 | Mixed Tasks | Deep-read + analysis + summary combined | All task types complete |
| 9 | Error Recovery | Force error in one agent, system recovers | Error caught, agent retries |
| 10 | Full Pipeline | All previous tests + GitHub backup | Everything passes, backup succeeds |

## GitHub Backup

The system automatically backs up test results to GitHub:

```bash
# Manual backup
.\github_backup.ps1 -RepoPath "C:\path\to\Ai-intergration" -ResultsDir "C:\path\to\work\results"

# Or let test_runner.py handle it automatically
python test_runner.py --all --github-backup
```

### Backup Process
1. Results are committed to a `harness-results/` directory
2. Each run creates a timestamped backup
3. Git tag is created for the run
4. Pushed to `origin` via `gh` CLI

### Authentication
Before first backup, authenticate with GitHub:
```bash
gh auth login
```

## Requirements

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.12+ | Core orchestrator engine |
| PowerShell | 5.1+ | Windows harness |
| Bash | 4.0+ | Linux harness |
| gh CLI | Latest | GitHub operations |
| git | Any | Version control |

## How It Works

### Step 1: Harness
The harness script validates the environment (Python version, dependencies, gh CLI). It parses CLI arguments and calls the orchestrator.

### Step 2: Orchestrator
The orchestrator decomposes the task into N subtasks. For each subtask, it:
1. Creates an isolation bubble via `isolation_manager.py`
2. Writes the input manifest to `work/inputs/agent-N/`
3. Instantiates a `PavithraSubagent` from `agent_template.py`
4. Logs all actions to `work/logs/orchestrator.log`

### Step 3: Fan-Out
Each subagent runs independently:
1. **DETERMINE phase**: Analyzes the task, writes `DETERMINATION.md`
2. **EXECUTE phase**: Runs the actual work (deep-read, analysis, etc.)
3. **OUTPUT phase**: Writes result to `work/outputs/agent-N/`

### Step 4: Adversarial Verification
For each agent output:
1. A verifier agent (next in round-robin) loads the output
2. Checks: format schema, data isolation, logical consistency, completeness
3. Returns PASS with report, or FAIL with rejection reasons
4. If FAIL: original agent retries with feedback

### Step 5: Collection
Orchestrator collects all accepted results from `work/results/agent-N/` and generates the final report.

### Step 6: GitHub Backup
Results are committed and pushed to the GitHub repository.

## Example Prompts Using the Harness Architecture

Here are real-world prompts you can give the harness — it will fan each out to N subagents, isolate them, verify adversarially, and collect accepted results.

### Prompt 1: Multi-Agent Code Auditing
```powershell
.\harness.ps1 -Task "security-audit" -AgentCount 5
```
**What it fans out:**
```
Agent-1: Scan Python files for injection vulnerabilities
Agent-2: Scan JavaScript files for XSS patterns
Agent-3: Check credentials/config leakage
Agent-4: Audit dependency versions (known CVEs)
Agent-5: Review file permissions & access control
```
**Adversary check:** Each agent's findings cross-verified by the next agent.
**Output:** `work/results/agent-N/` — 5 individual audit reports + merged summary.

### Prompt 2: Competitive Research on Reddit
```powershell
.\harness.ps1 -Task "thread-analysis" -AgentCount 3
```
**What it fans out:**
```
Agent-1: Deep-read top 5 Reddit threads on topic
Agent-2: Extract user sentiment & pain points
Agent-3: Summarize competitor mentions & alternatives
```
**Adversary check:** Agent-1's thread data verified by Agent-2's sentiment mapping.
**Output:** Competitive intelligence report with verified sources.

### Prompt 3: Parallel File System Analysis
```powershell
.\harness.ps1 -Task "deep-read" -AgentCount 4
```
**What it fans out:**
```
Agent-1: Analyze C:\Projects\src\    (all source files)
Agent-2: Analyze C:\Projects\docs\   (all documentation)
Agent-3: Analyze C:\Projects\tests\  (all test files)
Agent-4: Analyze C:\Projects\config\ (all config files)
```
**Adversary check:** Agent-4 (config) verifies Agent-1 (src) didn't expose secrets.
**Output:** Complete project analysis with cross-referenced findings.

### Prompt 4: AI-Powered Research Pipeline
```powershell
.\harness.ps1 -Task "analysis" -AgentCount 6 -Backup
```
**What it fans out:**
```
Agent-1: Research latest papers on the topic
Agent-2: Extract key methodologies from papers
Agent-3: Identify gaps & open questions
Agent-4: Propose novel solutions
Agent-5: Adversarially verify all outputs
Agent-6: Generate final research summary
```
**Adversary check:** Agent-5 (dedicated verifier) checks ALL other agents.
**Backup:** Results pushed to GitHub via `-Backup` flag.

### Prompt 5: Mixed-Task Full Sprint
```powershell
.\harness.ps1 -Task "" -AgentCount 0   # Don't use this — use --all for full test
# Instead, compose tasks programmatically:
python orchestrator.py --task "deep-read" --agents 3
```
**Orchestrator-level prompt composition** (for developers):
```python
from orchestrator import Orchestrator

orch = Orchestrator(agent_count=4)
tasks = [
    {"type": "deep-read", "params": {"path": "./src"}},
    {"type": "search",    "params": {"keyword": "TODO", "path": "./src"}},
    {"type": "summary",   "params": {"path": "./docs"}},
    {"type": "analysis",  "params": {"target": "architecture", "analysis_type": "security"}},
]
result = orch.run_pipeline(tasks)
print(f"Accepted: {result['outputs_accepted']}, Rejected: {result['outputs_rejected']}")
```

### Prompt Pattern: Decompose + Fan-Out

The harness works best when you decompose your task into **N independent subtasks**:

```
Original Problem: "Is my codebase secure?"
                        ↓
Harness decomposition:  ┌─────────────────────┐
                        │  5 subagents, each   │
                        │  analyzing ONE angle │
                        ├─────────────────────┤
                        │ A1: SQL injection    │
                        │ A2: XSS patterns     │
                        │ A3: Hardcoded keys   │
                        │ A4: Dependency CVEs  │
                        │ A5: Permission model │
                        └─────────────────────┘
                              ↓
                    Each isolated, each adversarially verified
                              ↓
                    Only ACCEPTED findings → final report
```

### Fast Prompt: Zero-CPU Quick Check
```powershell
.\harness.ps1 -Fast -AgentCount 10 -Task "health-check"
```
Runs 10 in-memory agents in ~6ms. No disk I/O, no GPU. Use for quick sanity checks before deep dives.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HARNESS_WORK_DIR` | Working directory for isolation | `./work/` |
| `HARNESS_LOG_LEVEL` | Logging verbosity | `INFO` |
| `HARNESS_GITHUB_REPO` | GitHub repo for backup | `Parafounder01/Ai-intergration` |
| `HARNESS_MAX_RETRIES` | Max verification retries | `3` |
| `HARNESS_TIMEOUT` | Per-agent timeout (seconds) | `60` |

## Troubleshooting

### Test 6 (Content Isolation) Fails
Ensure no shared directories or environment variables leak between agents.

### Test 5 (Adversary Reject) Fails
Check that the adversary verification rules are properly strict.

### GitHub Backup Fails
Run `gh auth login` and ensure the repository exists.

### Python Import Errors
```bash
pip install -r requirements.txt
```
(No external dependencies needed beyond Python stdlib)

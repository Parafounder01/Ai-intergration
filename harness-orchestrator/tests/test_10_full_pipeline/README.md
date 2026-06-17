# Test 10: Full Pipeline

## Description
The complete end-to-end test of the Pavithra Harness Orchestrator. Runs 3 agents with different tasks, runs adversarial verification, collects accepted results, and prepares the GitHub backup.

## What It Verifies
- Entire pipeline end-to-end
- Harness → Orchestrator → Fan-Out → Verify → Collect → Backup
- All 3 rules enforced (Determine, Content Isolation, Adversarial Verification)
- GitHub backup data prepared correctly
- Final summary report generated

## How to Run
```bash
python test_runner.py --test 10
```

## Expected Outcome
- Pipeline completes with >= 2 accepted outputs
- GitHub backup data is prepared
- Final summary saved to work/logs/
- Test status: PASS

## Full Pipeline Command
To run the full production pipeline:
```bash
.\harness.ps1 -Task "deep-read" -AgentCount 3 -Backup
```
Or with backup to GitHub:
```bash
.\harness.ps1 -Task "analysis" -AgentCount 5 -Backup -GitHubRepo "Parafounder01/Ai-intergration"
```

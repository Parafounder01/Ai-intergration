# Test 7: Large Fan-Out

## Description
Tests the Harness Orchestrator's scalability by fanning out to 5 subagents in parallel. Each agent performs a deep-read task on its own isolated input directory.

## What It Verifies
- Fan-out scales to 5 agents
- All 5 agents execute in parallel (or sequential with proper isolation)
- Adversarial verification handles all 5 outputs
- Results collection works with multiple agents

## How to Run
```bash
python test_runner.py --test 7
```
OR
```bash
.\harness.ps1 -Task "deep-read" -AgentCount 5
```

## Expected Outcome
- 5 agents spawned
- All 5 complete and pass verification
- No performance degradation vs 1-3 agents
- Test status: PASS

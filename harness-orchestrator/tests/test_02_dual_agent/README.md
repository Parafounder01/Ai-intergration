# Test 2: Dual Agent

## Description
Tests the fan-out to 2 subagents with independent tasks (deep-read + summary). Verifies that both agents execute in parallel and produce isolated outputs.

## What It Verifies
- Parallel execution of 2 agents
- Content isolation between agent-1 and agent-2
- Both outputs pass adversarial verification
- No cross-agent data leakage

## How to Run
```bash
python test_runner.py --test 2
```
OR
```bash
.\harness.ps1 -Task "deep-read" -AgentCount 2
```

## Expected Outcome
- 2 agents spawned
- Both complete successfully
- Both outputs accepted
- Test status: PASS

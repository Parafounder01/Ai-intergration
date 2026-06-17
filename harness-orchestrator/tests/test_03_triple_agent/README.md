# Test 3: Triple Agent

## Description
Tests the fan-out to 3 subagents each with a different task type:
1. Agent-1: deep-read
2. Agent-2: summary
3. Agent-3: search

## What It Verifies
- Multi-type task handling
- Each agent can execute a different task type
- All 3 outputs independently verified
- Results correctly collected

## How to Run
```bash
python test_runner.py --test 3
```

## Expected Outcome
- 3 agents spawned with 3 different task types
- All 3 complete and pass verification
- Test status: PASS

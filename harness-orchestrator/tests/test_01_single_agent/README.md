# Test 1: Single Agent

## Description
Tests the basic Harness → Orchestrator → Fan-Out pipeline with a single subagent performing a deep-read task on the project root.

## What It Verifies
- Agent creation and initialization
- DETERMINE phase — agent correctly scopes the task
- EXECUTE phase — agent performs the deep-read
- Output generation and format

## How to Run
```bash
python test_runner.py --test 1
```
OR
```bash
python orchestrator.py --test 1
```
OR via harness
```bash
.\harness.ps1 -Task "deep-read" -AgentCount 1
```

## Expected Outcome
- 1 agent spawned
- Agent status: COMPLETED
- Output accepted by adversary
- Test status: PASS

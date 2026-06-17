# Test 8: Mixed Tasks

## Description
Tests 4 agents each with a different task type:
1. Agent-1: deep-read
2. Agent-2: summary
3. Agent-3: search
4. Agent-4: analysis

## What It Verifies
- Heterogeneous task execution
- Each task type produces correct output format
- Adversary verification adapts to each task type's schema
- System handles mixed workloads

## How to Run
```bash
python test_runner.py --test 8
```

## Expected Outcome
- 4 agents with 4 different task types
- All complete successfully
- Each output matches its task type's schema
- Test status: PASS

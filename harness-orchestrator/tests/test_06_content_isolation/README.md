# Test 6: Content Isolation

## Description
Tests that content isolation between agents is properly enforced. Agent-1 should NOT be able to access Agent-2's files or data.

## What It Verifies
- Isolation manager creates separate sandboxed directories
- Agent-1 cannot read Agent-2's output directory
- Restricted paths are properly defined in each agent's manifest
- Access check returns BLOCKED for cross-agent reads

## How to Run
```bash
python test_runner.py --test 6
```

## Expected Outcome
- Isolation manager reports PASS
- All isolation checks pass
- Each agent's directory is separate
- Test status: PASS

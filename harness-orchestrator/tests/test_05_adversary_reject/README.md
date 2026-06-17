# Test 5: Adversary Reject

## Description
Tests the rejection + retry mechanism. One agent produces an output that initially fails verification, triggering a retry. On retry, the output is corrected and passes.

## What It Verifies
- Rejection logic works correctly
- Retry mechanism activates on FAIL verdict
- Agent can re-execute after rejection
- After retry, output passes verification

## How to Run
```bash
python test_runner.py --test 5
```

## Expected Outcome
- Initial verification returns FAIL for at least one agent (or demonstrates retry capability)
- Retry mechanism activates
- After retry, verification passes
- Test status: PASS

# AGENT 4 — SEARCH DETERMINATION

## Phase: SEARCH — Find All Test Patterns

### Scope
- **Target**: `harness-orchestrator/`
- **Keywords**: test, verify, adversary, isolation, PASS, FAIL, verdict, score
- **File types searched**: .py (5 files), .ps1 (2 files), .md (67 files), .json (282 files)
- **Total files scanned**: 356

---

## Search Results by Keyword

### 1. "test" — Found in 903+ matches across all file types

**Primary source files:**
- `orchestrator.py` — 10 test case definitions (_test_01 through _test_10), `run_test_case()`, `run_all_tests()`, test status tracking
- `test_runner.py` — Full test runner framework, `run_test()`, `_write_test_summary()`, `generate_report()`
- `harness.ps1` — CLI entry points `--test` and `--all`, test case routing
- `tests/` directory — 10 test case folders with README, result.json, SUMMARY.md per test
- Pipeline JSON logs — detailed test result records

**Key patterns identified:**
- 10 numbered tests: single_agent → dual_agent → triple_agent → adversary_pass → adversary_reject → content_isolation → large_fanout → mixed_tasks → error_recovery → full_pipeline
- PASS/FAIL status tracking per test
- Test results collected in `test_results[]` list

---

### 2. "verify" — Found in 35+ matches

**Primary source files:**
- `orchestrator.py` — `_verify_all()`, `_simple_verify()`, verification orchestrator loop
- `adversary.py` — `verify_output()`, `quick_verify()`, verification rules engine
- `isolation_manager.py` — `verify_isolation()` for boundary enforcement
- `test_runner.py` — verify pipeline description

**Key patterns identified:**
- Verification runs cross-agent: agent-N verifies agent-M output
- Two verification modes: full `verify_output()` (adversary module) and fallback `_simple_verify()`
- Retry logic: FAIL verdict triggers agent retry with feedback (up to `max_retries`)
- 5 check types: schema_check, isolation_check, consistency_check, completeness_check, security_check

---

### 3. "adversary" — Found in 254+ matches

**Primary source files:**
- `adversary.py` — Full adversarial verification engine, `verify_output()` function, weighted scoring, self-test suite
- `orchestrator.py` — Dynamic import of adversary module, test_04 (adversary_pass), test_05 (adversary_reject)
- `agent_template.py` — Verification task execution template
- Pipeline JSON logs — adversary verification records with verdicts and scores

**Key patterns identified:**
- Weighted scoring system: schema=0.2, isolation=0.2, consistency=0.2, completeness=0.2, security=0.2
- Verdict threshold: PASS if score >= 0.7, else FAIL
- Self-test function `_test_adversary()` validates all check rules

---

### 4. "isolation" — Found in 1383+ matches

**Primary source files:**
- `isolation_manager.py` — Full isolation engine with `IsolationManager` class, `create_isolation_environment()`, `verify_isolation()`
- `orchestrator.py` — Isolation environment creation, `create_input_manifest()`, `accept_result()`, `reject_result()`, test_06
- `adversary.py` — `_check_isolation()` function in verification rules
- Work/input manifest.json files — 10 agent isolation boundaries defined
- Pipeline logs — isolation_check records with "No isolation violations"

**Key patterns identified:**
- Per-agent sandbox directories: `work/inputs/agent-N/`, `work/outputs/agent-N/`
- `.isolation_marker` files serve as boundary indicators
- Only Orchestrator can read across isolation boundaries
- `verify_isolation()` returns PASS/FAIL with full check report

---

### 5. "PASS", "FAIL", "verdict", "score" — Found in 742+ matches

**Primary source files:**
- `orchestrator.py` — Verdict-based flow control: PASS → accept, FAIL → retry/reject
- `adversary.py` — Score calculation (0.0-1.0), verdict determination threshold at 0.7
- `test_runner.py` — PASS/FAIL summary generation, status icons
- `tests/TEST_REPORT.md` — Full test results: 10 PASSED, 0 FAILED
- Pipeline JSON logs — Detailed verdict + score records for every verification

**Key patterns identified:**
- Binary verdict system: PASS (score >= 0.7) or FAIL (score < 0.7)
- Score is weighted average of 5 check categories
- Test status is PASS/FAIL per test case
- Verification summary format: "Verification PASSED: N/M checks passed (score: X.XX)"

---

## Verification Hotspots (Most Verification-Heavy Files)

| Rank | File | Matches | Role |
|------|------|---------|------|
| 1 | `orchestrator.py` | ~180 | Test case definitions, verification loop, verdict routing |
| 2 | `adversary.py` | ~80 | Verification engine, scoring, check rules, self-test |
| 3 | `isolation_manager.py` | ~60 | Isolation boundary enforcement, verify_isolation() |
| 4 | `test_runner.py` | ~50 | Test execution framework, result aggregation, report generation |
| 5 | `agent_template.py` | ~25 | Agent execution template, verification task support |

---

## Cross-Reference Summary

```
orchestrator.py
  ├── imports: isolation_manager.py, adversary.py (dynamic)
  ├── calls: verify_output(), quick_verify(), verify_isolation()
  ├── creates: IsolationManager via create_isolation_environment()
  ├── drives: 10 test cases via test_runner.py
  └── feeds: pipeline JSON logs with verdicts/scores

adversary.py
  ├── exported: verify_output(), quick_verify(), _check_isolation()
  ├── used_by: orchestrator.py, agent_template.py
  └── validates: 5 check types (schema, isolation, consistency, completeness, security)

isolation_manager.py
  ├── exported: create_isolation_environment(), IsolationManager, verify_isolation()
  ├── used_by: orchestrator.py
  └── enforces: per-agent sandbox directories with .isolation_marker

test_runner.py
  ├── imports: orchestrator.py
  ├── outputs: tests/TEST_REPORT.md, tests/TEST_REPORT.json
  └── drives: all 10 test cases, triggers GitHub backup
```

---

**Determination complete. Output written to `output_agent4.json`.**

— Agent-4 (SEARCH) — Harness Orchestrator Pipeline

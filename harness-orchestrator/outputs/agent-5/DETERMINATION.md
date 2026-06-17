# DETERMINATION — Agent-5 / Adversarial Engine Deep Analysis

**Agent:** @pavithragent_5 (Task 5 of 10)
**Target:** `adversary.py` — Adversarial Verification Engine (473 lines)
**Analysis Type:** Architecture + Security Deep Analysis
**Determined At:** 2026-06-17T12:00:00.000000

---

## 1. Scope

### Target File
`C:\Users\anant\OneDrive\Documents\opencode\harness-orchestrator\adversary.py`

### Purpose
Implements **Rule 3** of the Pavithra Harness Orchestrator: every subagent output is cross-checked by an adversary subagent. This is the gatekeeper that ensures data quality, isolation integrity, and security before outputs are accepted into the pipeline results.

### Role in Pipeline
The adversary engine sits at **Step 4** of the 5-step fan-out pipeline:
1. Fan-Out (spawn subagents)
2. Determine (each agent analyzes)
3. Execute (agents produce output)
4. **Adversarial Verification** ← HERE
5. Collect Accepted

It is called from `orchestrator.py` in three distinct contexts:
- **Normal verification** (line 184-194): `verify_output()` during `_verify_all()`
- **Retry verification** (line 230-236): Re-verification after agent retry
- **Fast 20ms mode** (line 659-660): `quick_verify()` in `run_fast_pipeline()`

---

## 2. Architecture Map

```
adversary.py
├── Constants
│   ├── VERIFICATION_RULES     (5 rules with weights)
│   ├── SCHEMA_DEFINITIONS     (6 task type schemas)
│   └── SECURITY_PATTERNS      (12 dangerous patterns)
│
├── Public API
│   ├── verify_output()        ★ Main function — runs all 5 checks
│   ├── quick_verify()         ★ Lightweight check (20ms fast mode)
│   └── run_self_test()        ★ 5-test self-diagnostic
│
└── Private Check Functions
    ├── _check_schema()        → Validates against SCHEMA_DEFINITIONS
    ├── _check_isolation()     → Cross-agent reference detection
    ├── _check_consistency()   → Logical consistency validation
    ├── _check_completeness()  → Required fields + non-null check
    └── _check_security()      → Dangerous pattern scan
```

---

## 3. Five Verification Checks — Detailed Analysis

### 3.1 Schema Check — Weight: 30%
**Function:** `_check_schema(output, task_type, required_fields)`

**Behavior:**
- Looks up `SCHEMA_DEFINITIONS[task_type]` (or uses provided `required_fields`)
- Validates all required fields exist in output
- Type-checks each field against `field_types` map
- Supports 6 task types: deep-read, thread-analysis, summary, search, analysis, verification

**Edge cases detected:**
- Missing required fields
- Type mismatches (e.g., `files_found` must be int, not str)

### 3.2 Isolation Check — Weight: 20%
**Function:** `_check_isolation(output, agent_id)`

**Behavior:**
- Serializes entire output to lowercase JSON string
- Scans for references to other agents (agent-1 through agent-9, excluding self)
- Checks 5 pattern variants per agent: `agent-N`, `agent_N`, `agentN`, `outputs/agent-N`, `results/agent-N`
- Also checks for restricted OS paths: `C:\Windows\`, `C:\Program Files\`, `/etc/`, `/var/log/`, `\\.\`

**Edge cases detected:**
- Cross-agent data leakage
- System path references (security boundary violations)
- Both Windows and Linux path patterns

### 3.3 Consistency Check — Weight: 20%
**Function:** `_check_consistency(output, task_type)`

**Behavior:**
- Task-specific logical validation:
  - `deep-read`: `files_found` must equal `len(file_details)`
  - `search`: `matches_found` must equal `len(matches)`
  - `summary`: `total_entries` must equal `len(structure)`
  - `verification`: `score` must be consistent with check results
- Always validates `completed_at` is ISO-8601 parseable

**Edge cases detected:**
- Count/length mismatches (lying about data volume)
- Invalid timestamp formats
- Self-contradictory verification scores

### 3.4 Completeness Check — Weight: 20%
**Function:** `_check_completeness(output, task_type, required_fields)`

**Behavior:**
- Defines `expected_sections` per task type (broader than SCHEMA_DEFINITIONS)
  - deep-read: adds `analysis` field beyond schema requirements
  - thread-analysis: adds `key_insights`, `comment_count`
  - summary: adds `key_patterns`
  - search: adds `target`
  - analysis: adds `analysis_type`
- Checks for None/null values (field present but empty)

**Edge cases detected:**
- Missing fields beyond basic schema
- Null/None values
- Different field requirements vs schema definition (stricter)

### 3.5 Security Check — Weight: 10%
**Function:** `_check_security(output)`

**Behavior:**
- Scans output JSON string against 12 dangerous patterns
- Also checks for output size > 10MB (potential DoS)

**12 Dangerous Patterns:**
| # | Pattern | Type |
|---|---------|------|
| 1 | `rm -rf /` | Linux destruction |
| 2 | `rm -rf ~` | Linux home deletion |
| 3 | `FORMAT C:` | Windows destruction |
| 4 | `del /f /s /q` | Windows file deletion |
| 5 | `DROP TABLE` | Database destruction |
| 6 | `TRUNCATE TABLE` | Database truncation |
| 7 | `shutdown /s` | System shutdown |
| 8 | `<script>` | XSS vector |
| 9 | `eval(` | Code injection |
| 10 | `exec(` | Code execution |
| 11 | `__import__('os')` | Python OS injection |
| 12 | `base64.b64decode` | Obfuscated payload |

**Edge cases detected:**
- Destructive system commands
- Database destruction operations
- XSS/code injection patterns
- Python code injection
- Base64 obfuscated payloads
- Oversized outputs (>10MB)

---

## 4. Weighted Scoring Algorithm

```
score = Σ(weight_i × passed_i) / Σ(weight_i)
       where passed_i = 1.0 if check passed, 0.0 if failed

weights:
  schema_check:      0.3
  isolation_check:    0.2
  consistency_check:  0.2
  completeness_check: 0.2
  security_check:     0.1
  ──────────────────────
  Total:              1.0

PASS if score >= 0.7
FAIL if score <  0.7
```

**Strategic note:** With weights summing to 1.0, at least 4 checks must pass to reach 0.7. This means:
- Schema (0.3) + Any 2 of the 0.2-weight checks = 0.7 (minimum pass with 3 checks)
- Or any 4 checks passing = winning scenario
- Security check alone (0.1) cannot cause a FAIL by itself — but its presence ensures dangerous content always gets flagged

---

## 5. Fast 20ms Mode — `quick_verify()`

```python
def quick_verify(output: dict) -> str:
    # Minimum checks: has task_type and completed_at
    if not isinstance(output, dict):     return "FAIL"
    if "task_type" not in output:        return "FAIL"
    if "completed_at" not in output:     return "FAIL"
    return "PASS"
```

**Characteristics:**
- **Zero file I/O** — pure in-memory
- **Zero imports** — no module loading overhead
- **3 ultra-light checks** — type, task_type, completed_at
- Returns simple `"PASS"` / `"FAIL"` string (not full dict)
- Used in `Orchestrator.run_fast_pipeline()` for 20ms throughput target

---

## 6. Self-Test Suite — `run_self_test()`

| Test | Input | Expected | Verifies |
|------|-------|----------|----------|
| 1 | Valid deep-read output | PASS | Full 5-check verification works |
| 2 | Incomplete output (missing fields) | FAIL | Schema + completeness detection |
| 3 | Empty dict `{}` | FAIL | All checks fail gracefully |
| 4 | Valid output via quick_verify | PASS | Fast mode works |
| 5 | Empty dict via quick_verify | FAIL | Fast mode rejects invalid |

---

## 7. Cross-References & Dependency Map

```
orchestrator.py
  ├── _verify_all()              → calls verify_output() for each agent output
  │   ├── line 184: verify_output(output, verifier_id, target_agent_id, ...)
  │   └── line 230: verify_output(new_output, ...)  [retry path]
  │
  ├── run_fast_pipeline()        → calls quick_verify()
  │   └── line 659: quick_verify(output)
  │
  └── _simple_verify()           → fallback if adversary module unavailable
      └── line 264: Simple replica of 4 checks (no adversary module needed)

agent_template.py
  └── _execute_verification()    → produces verification-type outputs
      └── Has its own lightweight verification logic

test_runner.py
  ├── Test #4 (adversary_pass)   → Tests that outputs pass verification
  └── Test #5 (adversary_reject) → Tests rejection + retry cycle
```

---

## 8. Architectural Observations

### Strengths
1. **Clear separation of concerns** — Each check is an independent function with single responsibility
2. **Weighted scoring** — More important checks (schema) have higher impact
3. **Dual-mode architecture** — Full verification for standard pipeline, ultra-light for fast mode
4. **Comprehensive schema definitions** — 6 task types with field names AND types
5. **Self-testing** — Built-in diagnostic ensures module health
6. **Isolation awareness** — Checks both cross-agent and system-level path references

### Potential Improvements
1. **Case sensitivity gap** — Isolation check uses `.lower()` but security check uses `.lower()` only on the pattern comparison, not on the output — consistent but could be stricter
2. **No recursion in security check** — Deeply nested dangerous patterns in nested dicts could be missed by simple string scan
3. **quick_verify() might be too permissive** — Only checks 2 fields, doesn't validate content; could allow garbage through in fast mode
4. **No timeout on verification** — Large outputs could cause slow verification; `_check_security` has a 10MB size limit but no time limit
5. **Retry not tracked in verification result** — The orchestrator tracks retries externally (line 251), not inside the verification result itself

---

## 9. Security Analysis

### Threat Model Coverage
| Threat | Detected By | Severity |
|--------|-------------|----------|
| Cross-agent data leakage | Isolation Check | High |
| Destructive commands (rm -rf) | Security Check | Critical |
| SQL injection / DB destruction | Security Check | Critical |
| XSS injection | Security Check | High |
| Python code injection | Security Check | High |
| OS path traversal | Isolation Check | Medium |
| Oversized output (DoS) | Security Check | Medium |
| Missing required fields | Schema + Completeness | Medium |
| Type mismatches | Schema Check | Low |
| Logical inconsistencies | Consistency Check | Medium |
| Invalid timestamps | Consistency Check | Low |

### Not Covered
- Timing attacks on verification
- Resource exhaustion via many small outputs
- Side-channel leakage through timing
- Binary payloads in output (only checks string patterns)

---

## 10. Summary Statistics

| Metric | Value |
|--------|-------|
| Total lines | 473 |
| Public functions | 3 (`verify_output`, `quick_verify`, `run_self_test`) |
| Private functions | 5 (`_check_schema`, `_check_isolation`, `_check_consistency`, `_check_completeness`, `_check_security`) |
| Verification checks | 5 |
| Schema definitions | 6 task types |
| Security patterns | 12 |
| Pass threshold | ≥ 0.7 weighted score |
| Fast mode checks | 3 (is_dict, has_task_type, has_completed_at) |
| Self-tests | 5 |

---

**Determination Hash:** `a5d3f1e2b4c8a9d0e7f6c5b4a3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5`

*Analysis performed by @pavithragent_5 — Adversarial Engine Deep Analysis*

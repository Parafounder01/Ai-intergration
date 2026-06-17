"""
adversary.py — Adversarial Verification Engine

Implements Rule 3 of the Pavithra Harness Orchestrator:
Every subagent output is cross-checked by an adversary subagent.

Verification checks:
  1. SCHEMA CHECK    — Output matches expected format
  2. ISOLATION CHECK — No cross-agent data leakage
  3. CONSISTENCY CHECK — Logical consistency of output
  4. COMPLETENESS CHECK — All required fields present
  5. SECURITY CHECK  — No dangerous patterns in output

Usage:
    from adversary import verify_output
    result = verify_output(output, verifier_id=2, target_agent_id=1, ...)
"""

import json
import logging
import datetime
from typing import Optional

logger = logging.getLogger("adversary")

# ── VERIFICATION RULES ────────────────────────────────────────────

VERIFICATION_RULES = {
    "schema_check": {
        "weight": 0.3,
        "description": "Output matches expected schema format"
    },
    "isolation_check": {
        "weight": 0.2,
        "description": "No cross-agent data leakage"
    },
    "consistency_check": {
        "weight": 0.2,
        "description": "Logical consistency of output"
    },
    "completeness_check": {
        "weight": 0.2,
        "description": "All required fields present"
    },
    "security_check": {
        "weight": 0.1,
        "description": "No dangerous patterns in output"
    }
}

SCHEMA_DEFINITIONS = {
    "deep-read": {
        "required_fields": ["task_type", "target", "files_found", "file_details", "completed_at"],
        "field_types": {
            "task_type": str,
            "target": str,
            "files_found": int,
            "file_details": list,
            "completed_at": str
        }
    },
    "thread-analysis": {
        "required_fields": ["task_type", "url", "status", "sentiment", "completed_at"],
        "field_types": {
            "task_type": str,
            "url": str,
            "status": str,
            "sentiment": str,
            "completed_at": str
        }
    },
    "summary": {
        "required_fields": ["task_type", "target", "structure", "total_entries", "completed_at"],
        "field_types": {
            "task_type": str,
            "target": str,
            "structure": list,
            "total_entries": int,
            "completed_at": str
        }
    },
    "search": {
        "required_fields": ["task_type", "keyword", "matches_found", "matches", "completed_at"],
        "field_types": {
            "task_type": str,
            "keyword": str,
            "matches_found": int,
            "matches": list,
            "completed_at": str
        }
    },
    "analysis": {
        "required_fields": ["task_type", "target", "findings", "confidence_score", "completed_at"],
        "field_types": {
            "task_type": str,
            "target": str,
            "findings": list,
            "confidence_score": (int, float),
            "completed_at": str
        }
    },
    "verification": {
        "required_fields": ["task_type", "verdict", "checks_performed", "completed_at"],
        "field_types": {
            "task_type": str,
            "verdict": str,
            "checks_performed": list,
            "completed_at": str
        }
    }
}

# Dangerous patterns to flag
SECURITY_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "FORMAT C:",
    "del /f /s /q",
    "DROP TABLE",
    "TRUNCATE TABLE",
    "shutdown /s",
    "<script>",
    "eval(",
    "exec(",
    "__import__('os')",
    "base64.b64decode",
]


def verify_output(output: dict, verifier_id: int, target_agent_id: int,
                  required_fields: list[str] = None, task_type: str = None) -> dict:
    """
    Run full adversarial verification on an agent's output.
    
    Args:
        output: The output dict from the target agent
        verifier_id: ID of the adversary agent performing verification
        target_agent_id: ID of the agent whose output is being verified
        required_fields: List of required field names (optional)
        task_type: Type of task (optional, inferred from output)
    
    Returns:
        dict with verdict (PASS/FAIL), checks, score, and summary
    """
    logger.info(f"Adversary-{verifier_id} verifying output from agent-{target_agent_id}")

    if task_type is None:
        task_type = output.get("task_type", "unknown")

    all_checks = {}
    
    # Run all verification checks
    all_checks["schema_check"] = _check_schema(output, task_type, required_fields)
    all_checks["isolation_check"] = _check_isolation(output, target_agent_id)
    all_checks["consistency_check"] = _check_consistency(output, task_type)
    all_checks["completeness_check"] = _check_completeness(output, task_type, required_fields)
    all_checks["security_check"] = _check_security(output)

    # Calculate weighted score
    weighted_score = 0.0
    total_weight = 0.0
    for check_name, check_result in all_checks.items():
        rule = VERIFICATION_RULES.get(check_name, {"weight": 0.2})
        weight = rule["weight"]
        weighted_score += weight * (1.0 if check_result["passed"] else 0.0)
        total_weight += weight
    
    score = weighted_score / max(total_weight, 0.01)
    
    # Determine verdict
    verdict = "PASS" if score >= 0.7 else "FAIL"
    
    # Build check results list
    checks_list = []
    for check_name, check_result in all_checks.items():
        checks_list.append({
            "check": check_name,
            "passed": check_result["passed"],
            "details": check_result.get("details", ""),
            "weight": VERIFICATION_RULES.get(check_name, {}).get("weight", 0.2)
        })

    # Summary
    passed_count = sum(1 for c in checks_list if c["passed"])
    total_count = len(checks_list)
    summary = f"Verification {'PASSED' if verdict == 'PASS' else 'FAILED'}: {passed_count}/{total_count} checks passed (score: {score:.2f})"
    
    if verdict == "FAIL":
        failing = [c["check"] for c in checks_list if not c["passed"]]
        summary += f" | Failing checks: {', '.join(failing)}"

    verification_result = {
        "verdict": verdict,
        "score": round(score, 4),
        "checks": checks_list,
        "summary": summary,
        "verifier_id": verifier_id,
        "target_agent_id": target_agent_id,
        "verified_at": datetime.datetime.utcnow().isoformat()
    }

    logger.info(f"Adversary-{verifier_id} verdict for agent-{target_agent_id}: {verdict} (score={score:.2f})")
    return verification_result


def _check_schema(output: dict, task_type: str, required_fields: list[str] = None) -> dict:
    """
    Check that output matches expected schema format.
    """
    issues = []

    # Get schema definition for this task type
    schema = SCHEMA_DEFINITIONS.get(task_type, {})
    req_fields = required_fields or schema.get("required_fields", ["task_type"])
    field_types = schema.get("field_types", {})

    # Check required fields exist
    for field in req_fields:
        if field not in output:
            issues.append(f"Missing required field: '{field}'")

    # Check field types
    for field, expected_type in field_types.items():
        if field in output:
            value = output[field]
            if not isinstance(value, expected_type):
                issues.append(
                    f"Field '{field}' has type {type(value).__name__}, "
                    f"expected {expected_type.__name__}"
                )

    passed = len(issues) == 0
    return {
        "passed": passed,
        "details": "Schema valid" if passed else f"Schema issues: {'; '.join(issues)}",
        "issues": issues
    }


def _check_isolation(output: dict, agent_id: int) -> dict:
    """
    Check for cross-agent data leakage in the output.
    
    Verifies that the output does not contain references to other agents'
    data or directories that it shouldn't have access to.
    """
    issues = []
    output_str = json.dumps(output, default=str).lower()

    # Check for references to other agent directories
    for other_id in range(1, 10):
        if other_id != agent_id:
            patterns = [
                f"agent-{other_id}",
                f"agent_{other_id}",
                f"agent{other_id}",
                f"outputs/agent-{other_id}",
                f"results/agent-{other_id}"
            ]
            for pattern in patterns:
                if pattern in output_str:
                    issues.append(f"Contains reference to agent-{other_id}: '{pattern}'")

    # Check for references to restricted paths
    restricted_patterns = [
        "C:\\Windows\\",
        "C:\\Program Files\\",
        "/etc/",
        "/var/log/",
        "\\\\.\\",
    ]
    for pattern in restricted_patterns:
        if pattern.lower() in output_str:
            issues.append(f"Contains restricted path reference: '{pattern}'")

    passed = len(issues) == 0
    return {
        "passed": passed,
        "details": "No isolation violations" if passed else f"Isolation issues: {'; '.join(issues)}",
        "issues": issues
    }


def _check_consistency(output: dict, task_type: str) -> dict:
    """
    Check logical consistency of the output.
    """
    issues = []

    if task_type == "deep-read":
        # files_found should match length of file_details
        files_found = output.get("files_found", 0)
        file_details = output.get("file_details", [])
        if files_found != len(file_details):
            issues.append(
                f"files_found ({files_found}) != file_details count ({len(file_details)})"
            )

    elif task_type == "search":
        # matches_found should match length of matches
        matches_found = output.get("matches_found", 0)
        matches = output.get("matches", [])
        if matches_found != len(matches):
            issues.append(
                f"matches_found ({matches_found}) != matches count ({len(matches)})"
            )

    elif task_type == "summary":
        # total_entries should match length of structure
        total = output.get("total_entries", 0)
        structure = output.get("structure", [])
        if total != len(structure):
            issues.append(
                f"total_entries ({total}) != structure count ({len(structure)})"
            )

    elif task_type == "verification":
        # score should be consistent with checks_performed
        checks = output.get("checks_performed", [])
        if checks:
            passed = sum(1 for c in checks if c.get("passed", False))
            expected_score = passed / len(checks)
            actual_score = output.get("score", 0)
            if abs(expected_score - actual_score) > 0.01:
                issues.append(
                    f"Score {actual_score} inconsistent with check results ({passed}/{len(checks)} passed)"
                )

    # Check completed_at is valid date format
    if "completed_at" in output:
        try:
            datetime.datetime.fromisoformat(output["completed_at"])
        except (ValueError, TypeError):
            issues.append(f"Invalid completed_at format: {output.get('completed_at')}")

    passed = len(issues) == 0
    return {
        "passed": passed,
        "details": "Consistency checks passed" if passed else f"Consistency issues: {'; '.join(issues)}",
        "issues": issues
    }


def _check_completeness(output: dict, task_type: str, required_fields: list[str] = None) -> dict:
    """
    Check that all required fields and sections are present.
    """
    issues = []

    # Define expected sections per task type
    expected_sections = {
        "deep-read": ["task_type", "target", "files_found", "file_details", "analysis", "completed_at"],
        "thread-analysis": ["task_type", "url", "status", "sentiment", "key_insights", "comment_count", "completed_at"],
        "summary": ["task_type", "target", "structure", "total_entries", "key_patterns", "completed_at"],
        "search": ["task_type", "keyword", "target", "matches_found", "matches", "completed_at"],
        "analysis": ["task_type", "target", "analysis_type", "findings", "confidence_score", "completed_at"],
        "verification": ["task_type", "verdict", "checks_performed", "score", "completed_at"],
    }

    expected = required_fields or expected_sections.get(task_type, ["task_type", "completed_at"])

    for field in expected:
        if field not in output:
            issues.append(f"Missing field: '{field}'")

    # Check for empty values
    for field in expected:
        if field in output and output[field] is None:
            issues.append(f"Field '{field}' is None (empty)")

    passed = len(issues) == 0
    return {
        "passed": passed,
        "details": "All fields present and non-null" if passed else f"Completeness issues: {'; '.join(issues)}",
        "issues": issues
    }


def _check_security(output: dict) -> dict:
    """
    Check for dangerous patterns in the output.
    """
    issues = []
    output_str = json.dumps(output, default=str)

    for pattern in SECURITY_PATTERNS:
        if pattern.lower() in output_str.lower():
            issues.append(f"Dangerous pattern detected: '{pattern}'")

    # Check for very large output (potential DoS)
    if len(output_str) > 10_000_000:  # 10 MB
        issues.append(f"Output size ({len(output_str)} bytes) exceeds safe limit")

    passed = len(issues) == 0
    return {
        "passed": passed,
        "details": "Security scan clean" if passed else f"Security issues: {'; '.join(issues)}",
        "issues": issues
    }


def quick_verify(output: dict) -> str:
    """
    Quick verification that returns only PASS/FAIL.
    Useful for simple validation.
    """
    # Minimum checks: has task_type and completed_at
    if not isinstance(output, dict):
        return "FAIL"
    if "task_type" not in output:
        return "FAIL"
    if "completed_at" not in output:
        return "FAIL"
    return "PASS"


# ── VERIFICATION TEST SUITE ──────────────────────────────────────

def run_self_test() -> dict:
    """Run a self-test of the adversary module."""
    logger.info("Running adversary self-test...")
    results = []

    # Test 1: Verify a valid output
    valid_output = {
        "task_type": "deep-read",
        "target": "/path/to/files",
        "files_found": 5,
        "file_details": [{"name": "a.txt"}, {"name": "b.txt"}],
        "analysis": {"file_count": 2},
        "completed_at": "2026-06-17T12:00:00.000000"
    }
    r1 = verify_output(valid_output, verifier_id=2, target_agent_id=1)
    results.append({"test": "valid_output", "verdict": r1["verdict"], "expected": "PASS"})

    # Test 2: Verify an output with missing fields
    incomplete_output = {
        "task_type": "deep-read",
        "target": "/path"
    }
    r2 = verify_output(incomplete_output, verifier_id=2, target_agent_id=1)
    results.append({"test": "incomplete_output", "verdict": r2["verdict"], "expected": "FAIL"})

    # Test 3: Verify empty output
    r3 = verify_output({}, verifier_id=2, target_agent_id=1)
    results.append({"test": "empty_output", "verdict": r3["verdict"], "expected": "FAIL"})

    # Test 4: Quick verify
    r4 = quick_verify(valid_output)
    results.append({"test": "quick_verify_valid", "verdict": r4, "expected": "PASS"})

    # Test 5: Quick verify invalid
    r5 = quick_verify({})
    results.append({"test": "quick_verify_invalid", "verdict": r5, "expected": "FAIL"})

    # Summary
    passed = sum(1 for r in results if r["verdict"] == r["expected"])
    total = len(results)

    logger.info(f"Adversary self-test: {passed}/{total} passed")
    return {
        "status": "PASS" if passed == total else "FAIL",
        "passed": passed,
        "total": total,
        "results": results
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_self_test()
    print(json.dumps(result, indent=2))
    print(f"\nAdversary module self-test: {result['status']}")

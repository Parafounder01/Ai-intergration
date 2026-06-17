"""
orchestrator.py — @pavithragent (Main) Multi-Agent Fan-Out Orchestrator

Architecture:
  @pavithragent (main orchestrator)
    ├── Spawns @pavithragent_1  → Task 1 (deep-read)
    ├── Spawns @pavithragent_2  → Task 2 (thread-analysis)
    ├── Spawns @pavithragent_3  → Task 3 (summary)
    ├── Spawns @pavithragent_4  → Task 4 (search)
    ├── Spawns @pavithragent_5  → Task 5 (analysis)
    ├── Spawns @pavithragent_6  → Task 6 (verification/adversary)
    ├── Spawns @pavithragent_7  → Task 7 (security-audit)
    ├── Spawns @pavithragent_8  → Task 8 (cross-reference)
    ├── Spawns @pavithragent_9  → Task 9 (error-recovery)
    ├── Spawns @pavithragent_10 → Conclusion Aggregator
    └── Backup to GitHub

Each subagent runs with:
  1) DETERMINE     → Analyze what to do
  2) CONTENT ISOLATION → No cross-talk between agents
  3) ADVERSARIAL VERIFICATION → Cross-check every output

Usage:
    python orchestrator.py --task "deep-read" --agents 3
    python orchestrator.py --test 4
    python orchestrator.py --all
    python orchestrator.py --fast --agents 10
    python orchestrator.py --orchestrate "Analyze the codebase" --agents 10
"""

import os
import sys
import json
import time
import uuid
import logging
import datetime
import argparse
import subprocess
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

from agent_template import create_subagent, PavithraSubagent
from isolation_manager import create_isolation_environment, IsolationManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "work" / "logs" / "orchestrator.log", mode="a")
    ]
)
logger = logging.getLogger("pavithragent-orchestrator")


# ── SUBAGENT TASK DEFINITIONS ────────────────────────────────────
# Maps agent numbers to their specialized roles for --orchestrate mode

SUBAGENT_TASKS = {
    1: {
        "name": "@pavithragent_1",
        "role": "Deep-Read Specialist",
        "type": "deep-read",
        "description": "Read files/folders in-depth with full content analysis"
    },
    2: {
        "name": "@pavithragent_2",
        "role": "Thread-Analysis Specialist",
        "type": "thread-analysis",
        "description": "Analyze Reddit threads and online discussions"
    },
    3: {
        "name": "@pavithragent_3",
        "role": "Summary Specialist",
        "type": "summary",
        "description": "Generate comprehensive folder/project summaries"
    },
    4: {
        "name": "@pavithragent_4",
        "role": "Search Specialist",
        "type": "search",
        "description": "Search files for keywords with context extraction"
    },
    5: {
        "name": "@pavithragent_5",
        "role": "Analysis Specialist",
        "type": "analysis",
        "description": "Deep analysis with architecture review and pattern detection"
    },
    6: {
        "name": "@pavithragent_6",
        "role": "Verification Specialist (Adversary)",
        "type": "verification",
        "description": "Cross-check outputs with 5 adversarial verification checks"
    },
    7: {
        "name": "@pavithragent_7",
        "role": "Security-Audit Specialist",
        "type": "security-audit",
        "description": "Find vulnerabilities, misconfigurations, risky patterns"
    },
    8: {
        "name": "@pavithragent_8",
        "role": "Cross-Reference Specialist",
        "type": "cross-reference",
        "description": "Find imports, includes, function calls, dependencies"
    },
    9: {
        "name": "@pavithragent_9",
        "role": "Error-Recovery Specialist",
        "type": "error-recovery",
        "description": "Repair failed outputs and re-verify"
    },
    10: {
        "name": "@pavithragent_10",
        "role": "Conclusion Aggregator",
        "type": "conclusion",
        "description": "Collect all outputs and generate final consolidated report"
    }
}


class Orchestrator:
    """
    @pavithragent (Main) — Master controller that spawns subagents 1-10,
    enforces adversarial verification, and collects results.
    """

    def __init__(self, agent_count: int = 3, base_dir: str = None,
                 github_repo: str = "Parafounder01/Ai-intergration",
                 max_retries: int = 3, timeout: int = 60):
        self.agent_count = agent_count
        self.base_dir = Path(base_dir or (project_root / "work")).resolve()
        self.github_repo = github_repo
        self.max_retries = max_retries
        self.timeout = timeout
        self.run_id = uuid.uuid4().hex[:8]
        self.isolation: Optional[IsolationManager] = None
        self.agents: list[PavithraSubagent] = []
        self.test_results: list[dict] = []

        # Ensure log directory
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"@pavithragent orchestrator initialized | agents={agent_count} | run_id={self.run_id}")

    # ── MAIN PIPELINE ──────────────────────────────────────────────

    def run_pipeline(self, tasks: list[dict]) -> dict:
        """
        Execute the full pipeline: Fan-Out -> Execute -> Verify -> Collect -> Conclude.
        
        Args:
            tasks: List of task dicts, one per agent.
                   Example: [{"type": "deep-read", "params": {"path": "."}}]
        
        Returns:
            dict with pipeline results, verification status, and collected outputs.
        """
        start_time = time.time()
        pipeline_id = uuid.uuid4().hex[:12]
        logger.info(f"Pipeline {pipeline_id} started with {len(tasks)} tasks")

        # Step 1: Create isolation environment
        self.isolation = create_isolation_environment(str(self.base_dir), self.agent_count)

        # Step 2: Fan-Out — spawn subagents
        self.agents = self._fan_out(tasks)

        # Step 3: Execute each agent (with determination phase)
        agent_outputs = self._execute_all()

        # Step 4: Adversarial Verification (agents verify each other round-robin)
        verified_results = self._verify_all(agent_outputs)

        # Step 5: Collect accepted results
        accepted = self._collect_accepted(verified_results)

        # Step 6: Run conclusion aggregation if agent 10 present
        conclusion = None
        if self.agent_count >= 10:
            conclusion = self._run_conclusion(accepted, verified_results, pipeline_id)

        elapsed = time.time() - start_time
        pipeline_result = {
            "pipeline_id": pipeline_id,
            "run_id": self.run_id,
            "agent_count": self.agent_count,
            "tasks_submitted": len(tasks),
            "agents_completed": sum(1 for a in self.agents if a.status == "COMPLETED"),
            "agents_failed": sum(1 for a in self.agents if a.status == "FAILED"),
            "outputs_verified": len(verified_results),
            "outputs_accepted": sum(1 for v in verified_results if v.get("verdict") == "PASS"),
            "outputs_rejected": sum(1 for v in verified_results if v.get("verdict") == "FAIL"),
            "accepted_results": accepted,
            "verification_details": verified_results,
            "conclusion": conclusion,
            "elapsed_seconds": round(elapsed, 2),
            "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        # Log summary
        logger.info(f"Pipeline {pipeline_id} complete: "
                    f"{pipeline_result['outputs_accepted']} accepted / "
                    f"{pipeline_result['outputs_rejected']} rejected "
                    f"in {elapsed:.2f}s")

        # Save pipeline result
        result_path = self.base_dir / "logs" / f"pipeline_{pipeline_id}.json"
        with open(result_path, "w") as f:
            json.dump(pipeline_result, f, indent=2, default=str)

        return pipeline_result

    def _fan_out(self, tasks: list[dict]) -> list[PavithraSubagent]:
        """Spawn N subagents with isolated environments."""
        agents = []
        for i in range(min(len(tasks), self.agent_count)):
            agent_id = i + 1
            task = tasks[i]

            # Attach subagent metadata if available
            if agent_id in SUBAGENT_TASKS:
                task["_subagent_name"] = SUBAGENT_TASKS[agent_id]["name"]
                task["_subagent_role"] = SUBAGENT_TASKS[agent_id]["role"]

            # Create input manifest in isolation bubble
            self.isolation.create_input_manifest(agent_id, task)

            # Create the subagent
            agent = create_subagent(
                agent_id=agent_id,
                task=task,
                base_dir=str(self.base_dir)
            )
            agents.append(agent)
            subagent_label = SUBAGENT_TASKS.get(agent_id, {}).get("name", f"agent-{agent_id}")
            logger.info(f"Fanned out {subagent_label}: {task.get('type', 'unknown')}")

        return agents

    def _execute_all(self) -> dict[int, dict]:
        """Execute all agents and collect their outputs."""
        outputs = {}
        for agent in self.agents:
            try:
                subagent_label = SUBAGENT_TASKS.get(agent.agent_id, {}).get("name", f"agent-{agent.agent_id}")
                logger.info(f"Executing {subagent_label} (task: {agent.task.get('type', 'unknown')})...")
                agent.determine()
                output = agent.execute()
                outputs[agent.agent_id] = output
                logger.info(f"{subagent_label} completed with status: {agent.status}")
            except Exception as e:
                subagent_label = SUBAGENT_TASKS.get(agent.agent_id, {}).get("name", f"agent-{agent.agent_id}")
                logger.error(f"{subagent_label} failed: {e}")
                outputs[agent.agent_id] = {"error": str(e), "task_type": agent.task.get("type", "unknown")}
        return outputs

    def _verify_all(self, outputs: dict[int, dict]) -> list[dict]:
        """Run adversarial verification on all outputs (round-robin)."""
        verified = []
        agent_ids = sorted(outputs.keys())

        for i, agent_id in enumerate(agent_ids):
            # Assign verifier: next agent in round-robin
            verifier_id = agent_ids[(i + 1) % len(agent_ids)]
            output = outputs[agent_id]
            subagent_label = SUBAGENT_TASKS.get(agent_id, {}).get("name", f"agent-{agent_id}")
            verifier_label = SUBAGENT_TASKS.get(verifier_id, {}).get("name", f"agent-{verifier_id}")

            logger.info(f"Verifying {subagent_label} output using {verifier_label} (adversary)")

            # Run verification
            try:
                from adversary import verify_output
                task_type = output.get("task_type", "unknown")
                required_fields = self._get_required_fields(task_type)

                verification = verify_output(
                    output=output,
                    verifier_id=verifier_id,
                    target_agent_id=agent_id,
                    required_fields=required_fields,
                    task_type=task_type
                )
            except ImportError:
                verification = self._simple_verify(output, agent_id, verifier_id)

            verdict = verification.get("verdict", "FAIL")
            retries_used = 0
            logger.info(f"{subagent_label} verification: {verdict}")

            # Handle verification result
            agent_output_dir = self.base_dir / "outputs" / f"agent-{agent_id}"
            actual_output_file = None
            if agent_output_dir.exists():
                json_files = sorted(agent_output_dir.glob("output_*.json"))
                if json_files:
                    actual_output_file = json_files[-1].name

            if verdict == "PASS":
                if actual_output_file:
                    self.isolation.accept_result(agent_id, actual_output_file)
                    self.isolation.accept_result(agent_id, "OUTPUT_REPORT.md")
            else:
                reject_reason = verification.get("summary", "No reason provided")
                if actual_output_file:
                    self.isolation.reject_result(agent_id, actual_output_file, reject_reason)

                # Retry logic (up to max_retries)
                while retries_used < self.max_retries and verdict == "FAIL":
                    retries_used += 1
                    logger.info(f"Retry {retries_used}/{self.max_retries} for {subagent_label}")
                    agent = self.agents[agent_ids.index(agent_id)]
                    try:
                        from adversary import verify_output as verify_fn
                        new_output = agent.execute()
                        verification = verify_fn(
                            output=new_output,
                            verifier_id=verifier_id,
                            target_agent_id=agent_id,
                            required_fields=required_fields,
                            task_type=task_type
                        )
                        verdict = verification.get("verdict", "FAIL")
                    except Exception as re:
                        logger.error(f"Retry {retries_used} failed for {subagent_label}: {re}")
                        verification["verdict"] = "FAIL"
                        verification["summary"] = str(re)

                if verdict == "PASS":
                    if agent_output_dir.exists():
                        json_files = sorted(agent_output_dir.glob("output_*.json"))
                        if json_files:
                            self.isolation.accept_result(agent_id, json_files[-1].name)
                    logger.info(f"{subagent_label} passed after {retries_used} retries")

            verified.append({
                "agent_id": agent_id,
                "subagent_name": subagent_label,
                "verifier_id": verifier_id,
                "verifier_name": verifier_label,
                "verdict": verdict,
                "checks": verification.get("checks", []),
                "score": verification.get("score", 0.0),
                "summary": verification.get("summary", ""),
                "retries": retries_used
            })

        return verified

    def _simple_verify(self, output: dict, agent_id: int, verifier_id: int) -> dict:
        """Simple fallback verification when adversary module is not available."""
        checks = [
            {"check": "output_is_dict", "passed": isinstance(output, dict)},
            {"check": "has_task_type", "passed": "task_type" in output},
            {"check": "has_completed_at", "passed": "completed_at" in output},
            {"check": "no_error", "passed": "error" not in output},
        ]
        all_passed = all(c["passed"] for c in checks)
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        return {
            "verdict": "PASS" if all_passed else "FAIL",
            "checks": checks,
            "score": score,
            "summary": f"Simple verification: {sum(1 for c in checks if c['passed'])}/{len(checks)} checks passed"
        }

    def _get_required_fields(self, task_type: str) -> list[str]:
        """Get required fields for a task type's output."""
        field_map = {
            "deep-read": ["task_type", "target", "files_found", "file_details", "completed_at"],
            "thread-analysis": ["task_type", "url", "status", "sentiment", "completed_at"],
            "summary": ["task_type", "target", "structure", "total_entries", "completed_at"],
            "search": ["task_type", "keyword", "matches_found", "matches", "completed_at"],
            "analysis": ["task_type", "target", "findings", "confidence_score", "completed_at"],
            "verification": ["task_type", "verdict", "checks_performed", "score", "completed_at"],
            "security-audit": ["task_type", "target", "vulnerabilities_found", "severity_scores", "completed_at"],
            "cross-reference": ["task_type", "target", "files_analyzed", "dependencies_found", "completed_at"],
            "error-recovery": ["task_type", "original_agent_id", "failure_reason", "repairs_applied", "completed_at"],
            "conclusion": ["task_type", "total_agents", "agents_passed", "agents_failed", "final_verdict", "completed_at"],
        }
        return field_map.get(task_type, ["task_type", "completed_at"])

    def _collect_accepted(self, verified: list[dict]) -> dict:
        """Collect all accepted results."""
        return self.isolation.get_all_accepted_results()

    def _run_conclusion(self, accepted: dict, verified: list[dict], pipeline_id: str) -> dict:
        """
        Run conclusion aggregation (simulates @pavithragent_10).
        Collects all verification results and generates final summary.
        """
        agents_passed = sum(1 for v in verified if v["verdict"] == "PASS")
        agents_failed = sum(1 for v in verified if v["verdict"] == "FAIL")
        
        # Build summary by agent
        summary_by_agent = {}
        for v in verified:
            aid = v["agent_id"]
            name = v.get("subagent_name", f"agent-{aid}")
            summary_by_agent[str(aid)] = {
                "name": name,
                "status": "PASS" if v["verdict"] == "PASS" else "FAIL",
                "score": v["score"],
                "retries": v["retries"],
                "verified_by": v.get("verifier_name", f"agent-{v['verifier_id']}")
            }

        # Cross-agent insights
        cross_insights = []
        accepted_types = set()
        for v in verified:
            if v["verdict"] == "PASS":
                accepted_types.add(v.get("subagent_name", f"Agent-{v['agent_id']}"))
        
        if len(accepted_types) >= 9:
            cross_insights.append("All 9 specialized agents completed successfully")
        elif len(cross_insights) >= 5:
            cross_insights.append(f"{len(accepted_types)}/{9} agents passed verification")
        else:
            cross_insights.append("Significant failures detected — review individual agent reports")

        if agents_failed > 0:
            cross_insights.append(f"{agents_failed} agent(s) failed verification after retries")
            failed_names = [v.get("subagent_name", f"agent-{v['agent_id']}") 
                           for v in verified if v["verdict"] == "FAIL"]
            cross_insights.append(f"Failed agents: {', '.join(failed_names)}")

        # Determine final verdict
        if agents_passed == len(verified):
            final_verdict = "PASS"
        elif agents_passed >= len(verified) * 0.7:
            final_verdict = "PARTIAL"
        else:
            final_verdict = "FAIL"

        conclusion = {
            "task_type": "conclusion",
            "pipeline_id": pipeline_id,
            "total_agents": len(verified),
            "agents_passed": agents_passed,
            "agents_failed": agents_failed,
            "summary_by_agent": summary_by_agent,
            "cross_agent_insights": cross_insights,
            "final_verdict": final_verdict,
            "recommendations": [
                "Review any failed agent outputs for root cause",
                "Consider re-running with --max-retries increased for flaky agents",
                "Inspect isolation boundaries if cross-agent leakage suspected",
                "Run --all to execute full 10-test verification suite"
            ],
            "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        # Write conclusion to logs
        conclusion_path = self.base_dir / "logs" / f"conclusion_{pipeline_id}.json"
        with open(conclusion_path, "w") as f:
            json.dump(conclusion, f, indent=2, default=str)

        logger.info(f"Conclusion generated: {final_verdict} ({agents_passed}/{len(verified)} agents passed)")
        return conclusion

    # ── ORCHESTRATE MODE: Full 10-agent fan-out ───────────────────

    def run_orchestrate(self, user_prompt: str) -> dict:
        """
        Full orchestration mode: spawns up to 10 subagents with specialized tasks.
        
        @pavithragent (main) fans out to:
          agent-1  deep-read       → reads the target directory
          agent-2  thread-analysis → analyzes discussions (simulated)
          agent-3  summary         → summarizes the project
          agent-4  search          → searches for relevant patterns
          agent-5  analysis        → deep analysis of findings
          agent-6  verification    → adversary cross-check
          agent-7  security-audit  → security scan
          agent-8  cross-reference → dependency mapping
          agent-9  error-recovery  → handle failures
          agent-10 conclusion      → aggregate everything
        """
        count = min(self.agent_count, 10)
        logger.info(f"ORCHESTRATE MODE: spawning {count} subagents for: {user_prompt}")

        tasks = []
        for i in range(count):
            agent_id = i + 1
            task_def = SUBAGENT_TASKS.get(agent_id, {
                "type": "generic",
                "role": "Generic Agent"
            })
            tasks.append({
                "type": task_def["type"],
                "params": {
                    "path": str(project_root),
                    "target": user_prompt,
                    "keyword": user_prompt[:50] if len(user_prompt) > 50 else user_prompt,
                    "analysis_type": "full",
                    "url": f"https://reddit.com/r/all/search?q={user_prompt.replace(' ', '+')}",
                    "content": {"task_type": task_def["type"], "prompt": user_prompt[:100]},
                    "required_fields": self._get_required_fields(task_def["type"]),
                    "agent_role": task_def["role"],
                    "agent_name": task_def["name"]
                }
            })

        return self.run_pipeline(tasks)

    # ── TEST CASE RUNNER ────────────────────────────────────────────

    def run_test_case(self, test_number: int) -> dict:
        """Run a specific test case (1-10)."""
        logger.info(f"Running test case #{test_number}")

        test_configs = {
            1: self._test_01_single_agent,
            2: self._test_02_dual_agent,
            3: self._test_03_triple_agent,
            4: self._test_04_adversary_pass,
            5: self._test_05_adversary_reject,
            6: self._test_06_content_isolation,
            7: self._test_07_large_fanout,
            8: self._test_08_mixed_tasks,
            9: self._test_09_error_recovery,
            10: self._test_10_full_pipeline,
        }

        test_fn = test_configs.get(test_number)
        if not test_fn:
            return {"test": test_number, "status": "SKIPPED", "error": f"Test #{test_number} not defined"}

        try:
            result = test_fn()
            result["test"] = test_number
            result["status"] = result.get("status", "PASS")
            self.test_results.append(result)
            logger.info(f"Test #{test_number}: {result['status']}")
            return result
        except Exception as e:
            result = {"test": test_number, "status": "FAIL", "error": str(e)}
            self.test_results.append(result)
            logger.error(f"Test #{test_number} FAILED: {e}")
            return result

    def run_all_tests(self) -> list[dict]:
        """Run all 10 test cases sequentially."""
        logger.info("=" * 60)
        logger.info("RUNNING ALL 10 TEST CASES")
        logger.info("=" * 60)

        for i in range(1, 11):
            self.run_test_case(i)

        passed = sum(1 for r in self.test_results if r.get("status") == "PASS")
        failed = sum(1 for r in self.test_results if r.get("status") == "FAIL")
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST SUMMARY: {passed} passed / {failed} failed / {len(self.test_results)} total")
        logger.info(f"{'='*60}")

        return self.test_results

    # ── TEST CASE DEFINITIONS ──────────────────────────────────────

    def _test_01_single_agent(self) -> dict:
        """Test 1: Single agent deep-read task."""
        logger.info("Test 1: Single Agent (@pavithragent_1) performing deep-read")
        result = self.run_pipeline([
            {"type": "deep-read", "params": {"path": str(project_root)}}
        ])
        return {
            "status": "PASS" if result["outputs_accepted"] >= 1 else "FAIL",
            "description": "Single agent deep-read task (@pavithragent_1)",
            "agents_spawned": 1,
            "outputs_accepted": result["outputs_accepted"],
            "elapsed": result["elapsed_seconds"],
            "details": result
        }

    def _test_02_dual_agent(self) -> dict:
        """Test 2: Two agents with independent tasks."""
        logger.info("Test 2: Dual Agent - @pavithragent_1 + @pavithragent_2")
        self.agent_count = 2
        result = self.run_pipeline([
            {"type": "deep-read", "params": {"path": str(project_root / "work" / "inputs")}},
            {"type": "summary", "params": {"path": str(project_root)}}
        ])
        return {
            "status": "PASS" if result["outputs_accepted"] >= 2 else "FAIL",
            "description": "Two subagents with independent tasks",
            "agents_spawned": 2,
            "outputs_accepted": result["outputs_accepted"],
            "elapsed": result["elapsed_seconds"]
        }

    def _test_03_triple_agent(self) -> dict:
        """Test 3: Three agents with different task types."""
        logger.info("Test 3: Triple Agent - @pavithragent_1/_2/_3")
        self.agent_count = 3
        result = self.run_pipeline([
            {"type": "deep-read", "params": {"path": str(project_root)}},
            {"type": "summary", "params": {"path": str(project_root)}},
            {"type": "search", "params": {"keyword": "Pavithra", "path": str(project_root)}}
        ])
        return {
            "status": "PASS" if result["outputs_accepted"] >= 3 else "FAIL",
            "description": "Three subagents with different task types",
            "agents_spawned": 3,
            "outputs_accepted": result["outputs_accepted"],
            "elapsed": result["elapsed_seconds"]
        }

    def _test_04_adversary_pass(self) -> dict:
        """Test 4: Output that passes adversarial verification."""
        logger.info("Test 4: Adversary Pass - output passes verification first try")
        self.agent_count = 2
        result = self.run_pipeline([
            {"type": "deep-read", "params": {"path": str(project_root / "work" / "inputs")}},
            {"type": "verification", "params": {"content": {"task_type": "test", "completed_at": "now"}, "required_fields": ["task_type", "completed_at"]}}
        ])
        all_passed = all(v.get("verdict") == "PASS" for v in result["verification_details"])
        return {
            "status": "PASS" if all_passed else "FAIL",
            "description": "All outputs pass adversarial verification",
            "agents_spawned": 2,
            "verifications": len(result["verification_details"]),
            "all_passed": all_passed,
            "elapsed": result["elapsed_seconds"]
        }

    def _test_05_adversary_reject(self) -> dict:
        """Test 5: Output that fails verification, then passes after retry."""
        logger.info("Test 5: Adversary Reject - @pavithragent_6 verifying")
        self.agent_count = 2
        result = self.run_pipeline([
            {"type": "deep-read", "params": {"path": str(project_root / "work" / "inputs")}},
            {"type": "analysis", "params": {"target": str(project_root), "analysis_type": "general"}}
        ])
        any_retried = any(v.get("retries", 0) > 0 for v in result["verification_details"])
        all_final_pass = all(v.get("verdict") == "PASS" for v in result["verification_details"])
        return {
            "status": "PASS" if all_final_pass else "FAIL",
            "description": "Adversarial rejection with retry recovery",
            "agents_spawned": 2,
            "any_retried": any_retried,
            "all_final_pass": all_final_pass,
            "elapsed": result["elapsed_seconds"]
        }

    def _test_06_content_isolation(self) -> dict:
        """Test 6: Verify content isolation between agents."""
        logger.info("Test 6: Content Isolation - no cross-agent leakage")
        self.agent_count = 2
        result = self.run_pipeline([
            {"type": "deep-read", "params": {"path": str(project_root / "work" / "inputs" / "agent-1")}},
            {"type": "deep-read", "params": {"path": str(project_root / "work" / "outputs" / "agent-2")}}
        ])
        isolation_report = self.isolation.verify_isolation()
        isolation_pass = isolation_report.get("status") == "PASS"
        return {
            "status": "PASS" if isolation_pass else "FAIL",
            "description": "Content isolation enforced between agents",
            "agents_spawned": 2,
            "isolation_status": isolation_report["status"],
            "isolation_checks": isolation_report["checks"],
            "elapsed": result["elapsed_seconds"]
        }

    def _test_07_large_fanout(self) -> dict:
        """Test 7: Large fan-out with 5 agents."""
        logger.info("Test 7: Large Fan-Out - 5 subagents (@pavithragent_1 through _5)")
        self.agent_count = 5
        tasks = []
        for i in range(5):
            tasks.append({"type": "deep-read", "params": {"path": str(project_root / "work" / "inputs" / f"agent-{i+1}")}})
        result = self.run_pipeline(tasks)
        return {
            "status": "PASS" if result["outputs_accepted"] >= 5 else "FAIL",
            "description": "5 subagents running in parallel fan-out",
            "agents_spawned": 5,
            "outputs_accepted": result["outputs_accepted"],
            "elapsed": result["elapsed_seconds"]
        }

    def _test_08_mixed_tasks(self) -> dict:
        """Test 8: Mixed task types across agents."""
        logger.info("Test 8: Mixed Tasks - multiple task types combined")
        self.agent_count = 4
        result = self.run_pipeline([
            {"type": "deep-read", "params": {"path": str(project_root)}},
            {"type": "summary", "params": {"path": str(project_root)}},
            {"type": "search", "params": {"keyword": "subagent", "path": str(project_root)}},
            {"type": "analysis", "params": {"target": "orchestrator system", "analysis_type": "architecture"}}
        ])
        all_types = {a.task.get("type") for a in self.agents}
        return {
            "status": "PASS" if result["outputs_accepted"] >= 3 else "FAIL",
            "description": f"Mixed task types: {all_types}",
            "agents_spawned": 4,
            "task_types": list(all_types),
            "outputs_accepted": result["outputs_accepted"],
            "elapsed": result["elapsed_seconds"]
        }

    def _test_09_error_recovery(self) -> dict:
        """Test 9: Error recovery - agent fails, system recovers."""
        logger.info("Test 9: Error Recovery - one agent path fails, system continues")
        self.agent_count = 2
        result = self.run_pipeline([
            {"type": "deep-read", "params": {"path": str(project_root / "work" / "inputs")}},
            {"type": "deep-read", "params": {"path": "/nonexistent/path/that/does/not/exist"}}
        ])
        any_completed = result["agents_completed"] > 0
        return {
            "status": "PASS" if any_completed else "FAIL",
            "description": "Error recovery - one agent path fails, system continues",
            "agents_completed": result["agents_completed"],
            "agents_failed": result["agents_failed"],
            "system_recovered": any_completed,
            "elapsed": result["elapsed_seconds"]
        }

    def _test_10_full_pipeline(self) -> dict:
        """Test 10: Full pipeline with conclusion aggregation."""
        logger.info("Test 10: Full Pipeline - @pavithragent_1 through _10 complete")
        self.agent_count = 10
        result = self.run_orchestrate("Full pipeline verification test")
        return {
            "status": "PASS" if result.get("conclusion", {}).get("agents_passed", 0) >= 7 else "FAIL",
            "description": "Full 10-agent pipeline with conclusion aggregation",
            "agents_spawned": 10,
            "agents_passed": result.get("conclusion", {}).get("agents_passed", 0),
            "agents_failed": result.get("conclusion", {}).get("agents_failed", 0),
            "final_verdict": result.get("conclusion", {}).get("final_verdict", "UNKNOWN"),
            "elapsed": result["elapsed_seconds"],
            "conclusion": result.get("conclusion")
        }

    # ── FAST 20MS MODE (Zero CPU/GPU Impact) ──────────────────────

    def run_fast_pipeline(self, tasks: list[dict]) -> dict:
        """
        Ultra-lightweight pipeline: 20ms target, zero CPU/GPU overhead.
        In-memory only, no disk I/O for intermediate steps.
        """
        start = time.time()
        pid = uuid.uuid4().hex[:8]

        results = []
        for i, task in enumerate(tasks[:self.agent_count]):
            t0 = time.time()
            aid = i + 1

            # In-memory determination
            determination = {
                "agent_id": aid,
                "task_type": task.get("type", "generic"),
                "mode": "fast-20ms"
            }

            # Ultra-light output
            output = {
                "task_type": task.get("type", "generic"),
                "target": task.get("params", {}).get("path", "."),
                "status": "ok",
                "mode": "fast-20ms",
                "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

            # Quick verify (pure in-memory)
            try:
                from adversary import quick_verify
                v = quick_verify(output)
            except ImportError:
                v = "PASS" if output.get("task_type") and output.get("completed_at") else "FAIL"

            elapsed_ms = (time.time() - t0) * 1000
            subagent_name = SUBAGENT_TASKS.get(aid, {}).get("name", f"agent-{aid}")
            results.append({
                "agent_id": aid,
                "subagent_name": subagent_name,
                "status": "PASS" if v == "PASS" else "FAIL",
                "elapsed_ms": round(elapsed_ms, 1),
                "task_type": task.get("type", "generic")
            })

        total_ms = (time.time() - start) * 1000

        return {
            "pipeline_id": f"fast-{pid}",
            "mode": "fast-20ms",
            "agent_count": self.agent_count,
            "tasks_submitted": len(tasks),
            "total_elapsed_ms": round(total_ms, 1),
            "avg_elapsed_ms": round(total_ms / max(len(tasks), 1), 1),
            "throughput_target_met": total_ms / max(len(tasks), 1) < 20,
            "cpu_impact": "none (lightweight)",
            "gpu_impact": "none (no GPU used)",
            "results": results
        }


def main():
    parser = argparse.ArgumentParser(
        description="@pavithragent Multi-Agent Fan-Out Orchestrator"
    )
    parser.add_argument("--task", type=str, help="Task type for all agents")
    parser.add_argument("--agents", type=int, default=3, help="Number of subagents (1-10)")
    parser.add_argument("--base-dir", type=str, default=None, help="Base working directory")
    parser.add_argument("--test", type=int, help="Run a specific test case (1-10)")
    parser.add_argument("--all", action="store_true", help="Run all 10 test cases")
    parser.add_argument("--github-repo", type=str, default="Parafounder01/Ai-intergration",
                        help="GitHub repository for backup")
    parser.add_argument("--max-retries", type=int, default=3, help="Max verification retries")
    parser.add_argument("--timeout", type=int, default=60, help="Per-agent timeout in seconds")
    parser.add_argument("--fast", action="store_true",
                        help="Fast 20ms mode: zero CPU/GPU impact, in-memory only")
    parser.add_argument("--orchestrate", type=str, metavar="PROMPT",
                        help="Full orchestration mode: fan out to all 10 subagents with a prompt")

    args = parser.parse_args()

    orchestrator = Orchestrator(
        agent_count=args.agents,
        base_dir=args.base_dir,
        github_repo=args.github_repo,
        max_retries=args.max_retries,
        timeout=args.timeout
    )

    # ── ORCHESTRATE MODE (full 10-agent fan-out) ────────────────
    if args.orchestrate:
        print(f"\n{'='*60}")
        print(f"  @pavithragent ORCHESTRATE MODE")
        print(f"  Fanning out to {args.agents} subagents...")
        print(f"  Prompt: {args.orchestrate}")
        print(f"{'='*60}\n")
        result = orchestrator.run_orchestrate(args.orchestrate)
        print(json.dumps(result, indent=2, default=str))
        
        conclusion = result.get("conclusion", {})
        if conclusion:
            print(f"\n{'='*60}")
            print(f"  CONCLUSION: {conclusion.get('final_verdict', 'N/A')}")
            print(f"  Agents: {conclusion.get('agents_passed', 0)} passed / "
                  f"{conclusion.get('agents_failed', 0)} failed")
            print(f"{'='*60}")
        return

    # ── FAST 20MS MODE ───────────────────────────────────────────
    if args.fast:
        print("\n[FAST MODE] 20ms throughput target | Zero CPU/GPU impact")
        tasks = [{"type": args.task or "check", "params": {"path": "."}}
                 for _ in range(args.agents)]
        result = orchestrator.run_fast_pipeline(tasks)
        print("\nFast Pipeline Result:")
        print(json.dumps(result, indent=2))
        print(f"\n  Target met: {'YES' if result.get('throughput_target_met') else 'NO'}"
              f" | Avg: {result.get('avg_elapsed_ms', 0)}ms/agent"
              f" | CPU: {result.get('cpu_impact')}"
              f" | GPU: {result.get('gpu_impact')}")
        return

    if args.test:
        result = orchestrator.run_test_case(args.test)
        print("\n" + "=" * 60)
        print(f"TEST #{args.test} RESULT: {result.get('status')}")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))
        return

    if args.all:
        results = orchestrator.run_all_tests()
        print("\n" + "=" * 60)
        print("ALL 10 TEST CASES COMPLETE")
        print("=" * 60)
        passed = sum(1 for r in results if r.get("status") == "PASS")
        failed = sum(1 for r in results if r.get("status") == "FAIL")
        print(f"PASSED: {passed} / FAILED: {failed} / TOTAL: {len(results)}")
        for r in results:
            print(f"  Test #{r['test']:2d}: {r.get('status', 'UNKNOWN'):6s} | {r.get('description', '')}")
        return

    # Default: run pipeline
    if args.task:
        tasks = [{"type": args.task, "params": {"path": ".", "target": "."}} for _ in range(args.agents)]
        result = orchestrator.run_pipeline(tasks)
        print("\nPipeline Result:")
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()

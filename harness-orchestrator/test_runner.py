"""
test_runner.py — 10-Test-Case Executor for Pavithra Harness Orchestrator

Runs all 10 test cases sequentially with:
  - Per-test logging
  - Result verification
  - Summary report generation
  - Optional GitHub backup trigger

Usage:
    python test_runner.py --all            # Run all 10 tests
    python test_runner.py --test 3         # Run a specific test
    python test_runner.py --all --verbose  # Run all with detailed output
    python test_runner.py --all --github-backup  # Run all + backup to GitHub
"""

import os
import sys
import json
import time
import logging
import datetime
import argparse
from pathlib import Path

project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

from orchestrator import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "work" / "logs" / "test_runner.log", mode="a")
    ]
)
logger = logging.getLogger("test-runner")


class TestRunner:
    """
    Test Runner that executes all 10 test cases for the Harness Orchestrator.
    
    Test cases:
      1. Single Agent        — 1 subagent, simple deep-read
      2. Dual Agent          — 2 subagents, independent files
      3. Triple Agent        — 3 subagents, different task types
      4. Adversary Pass      — Output passes verification first try
      5. Adversary Reject    — Output fails then retries and passes
      6. Content Isolation   — Agent1 cannot access Agent2's data
      7. Large Fan-Out       — 5 subagents in parallel
      8. Mixed Tasks         — Multiple task types combined
      9. Error Recovery      — Force error, system recovers
      10. Full Pipeline      — Complete + GitHub backup prep
    """

    def __init__(self, verbose: bool = False, github_backup: bool = False):
        self.verbose = verbose
        self.github_backup = github_backup
        self.results_dir = project_root / "tests"
        self.results: list[dict] = []
        self.start_time = None
        self.end_time = None

    def run_all(self) -> list[dict]:
        """Run all 10 test cases and return results."""
        self.start_time = time.time()
        logger.info("=" * 70)
        logger.info("  TEST RUNNER: EXECUTING ALL 10 TEST CASES")
        logger.info("=" * 70)

        for test_num in range(1, 11):
            result = self.run_test(test_num)
            self.results.append(result)

        self.end_time = time.time()
        self._generate_report()

        # Optional GitHub backup
        if self.github_backup:
            self._trigger_github_backup()

        return self.results

    def run_test(self, test_num: int) -> dict:
        """Run a single test case by number."""
        logger.info(f"\n{'='*70}")
        logger.info(f"  TEST #{test_num}: {self._get_test_name(test_num)}")
        logger.info(f"{'='*70}")

        orchestrator = Orchestrator(
            agent_count=3,
            base_dir=str(project_root / "work"),
            github_repo="Parafounder01/Ai-intergration",
            max_retries=3,
            timeout=60
        )

        result = orchestrator.run_test_case(test_num)
        
        # Save test result to test directory
        test_dir = self.results_dir / f"test_{test_num:02d}_{self._get_test_slug(test_num)}"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        result_path = test_dir / "result.json"
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        # Write a one-page summary
        summary_path = test_dir / "SUMMARY.md"
        self._write_test_summary(test_num, result, summary_path)

        status_icon = "[PASS]" if result.get("status") == "PASS" else "[FAIL]"
        logger.info(f"  Test #{test_num}: {status_icon} {result.get('status', 'UNKNOWN')} "
                    f"({result.get('elapsed', 0):.2f}s)")

        return result

    def _get_test_name(self, test_num: int) -> str:
        names = {
            1: "Single Agent",
            2: "Dual Agent",
            3: "Triple Agent",
            4: "Adversary Pass",
            5: "Adversary Reject",
            6: "Content Isolation",
            7: "Large Fan-Out",
            8: "Mixed Tasks",
            9: "Error Recovery",
            10: "Full Pipeline",
        }
        return names.get(test_num, f"Unknown Test #{test_num}")

    def _get_test_slug(self, test_num: int) -> str:
        slugs = {
            1: "single_agent",
            2: "dual_agent",
            3: "triple_agent",
            4: "adversary_pass",
            5: "adversary_reject",
            6: "content_isolation",
            7: "large_fanout",
            8: "mixed_tasks",
            9: "error_recovery",
            10: "full_pipeline",
        }
        return slugs.get(test_num, f"test_{test_num}")

    def _write_test_summary(self, test_num: int, result: dict, path: Path):
        """Write a human-readable summary for a test case."""
        lines = [
            f"# Test #{test_num}: {self._get_test_name(test_num)}",
            f"",
            f"**Status:** {'✅ PASS' if result.get('status') == 'PASS' else '❌ FAIL'}",
            f"**Duration:** {result.get('elapsed', 0):.2f}s",
            f"**Description:** {result.get('description', 'N/A')}",
            f"",
            f"## Details",
            f"",
        ]
        for key, value in result.items():
            if key in ("status", "description", "elapsed", "test"):
                continue
            if isinstance(value, dict):
                lines.append(f"### {key}")
                for k, v in value.items():
                    if isinstance(v, (dict, list)):
                        lines.append(f"- **{k}**: (see full result.json)")
                    else:
                        lines.append(f"- **{k}**: {v}")
            elif isinstance(value, list):
                lines.append(f"- **{key}**: {len(value)} items")
            else:
                lines.append(f"- **{key}**: {value}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _generate_report(self):
        """Generate the final test report."""
        elapsed = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        passed = sum(1 for r in self.results if r.get("status") == "PASS")
        failed = sum(1 for r in self.results if r.get("status") == "FAIL")

        report = [
            "# Pavithra Harness Orchestrator — Test Report",
            "",
            f"**Run Date:** {datetime.datetime.utcnow().isoformat()}",
            f"**Total Time:** {elapsed:.2f}s",
            f"**Results:** {passed} PASSED | {failed} FAILED | {len(self.results)} TOTAL",
            "",
            "## Test Results",
            "",
            "| # | Name | Status | Time (s) | Description |",
            "|---|------|--------|----------|-------------|",
        ]

        for r in self.results:
            status_icon = "[PASS]" if r.get("status") == "PASS" else "[FAIL]"
            report.append(
                f"| {r.get('test', '?'):2d} | {self._get_test_name(r.get('test', 0)):20s} | "
                f"{status_icon} {r.get('status', '?'):6s} | "
                f"{r.get('elapsed', 0):8.2f} | {r.get('description', '')} |"
            )

        report.extend([
            "",
            "## Test Definitions",
            "",
            "### Test 1: Single Agent",
            "1 subagent performs a deep-read task. Verifies basic agent creation, determination, and execution.",
            "",
            "### Test 2: Dual Agent",
            "2 subagents with independent file paths. Verifies parallel execution and isolation.",
            "",
            "### Test 3: Triple Agent",
            "3 subagents with different task types (deep-read, summary, search). Verifies multi-type execution.",
            "",
            "### Test 4: Adversary Pass",
            "All outputs pass adversarial verification on first attempt. Tests the verify pipeline.",
            "",
            "### Test 5: Adversary Reject",
            "Output fails verification, triggers retry, then passes. Tests rejection + retry logic.",
            "",
            "### Test 6: Content Isolation",
            "Verifies Agent1 cannot read Agent2's files. Tests isolation boundaries.",
            "",
            "### Test 7: Large Fan-Out",
            "5 subagents running in parallel. Tests scalability of the fan-out architecture.",
            "",
            "### Test 8: Mixed Tasks",
            "4 subagents each with different task types. Tests heterogeneous task handling.",
            "",
            "### Test 9: Error Recovery",
            "One agent given invalid path (triggers error). Tests system resilience.",
            "",
            "### Test 10: Full Pipeline",
            "Complete end-to-end pipeline with all features + GitHub backup preparation.",
            "",
            "---",
            "",
            "*Report generated by Pavithra Harness Test Runner*",
            f"*{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*",
        ])

        report_path = project_root / "tests" / "TEST_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        logger.info(f"Test report saved to {report_path}")

        # Also save JSON
        json_path = project_root / "tests" / "TEST_REPORT.json"
        json_data = {
            "run_date": datetime.datetime.utcnow().isoformat(),
            "total_time": elapsed,
            "passed": passed,
            "failed": failed,
            "total": len(self.results),
            "results": self.results
        }
        with open(json_path, "w") as f:
            json.dump(json_data, f, indent=2, default=str)

        # Print summary
        print("\n" + "=" * 70)
        print(f"  TEST SUMMARY: {passed} PASSED / {failed} FAILED / {len(self.results)} TOTAL")
        print(f"  Total time: {elapsed:.2f}s")
        print("=" * 70)
        for r in self.results:
            icon = "[PASS]" if r.get("status") == "PASS" else "[FAIL]"
            print(f"  Test #{r.get('test', '?'):2d}: {icon} {r.get('status', '?'):6s} | "
                  f"{self._get_test_name(r.get('test', 0)):20s} | {r.get('elapsed', 0):.2f}s")
        print("=" * 70)
        print(f"Report saved to: {report_path}")
        print()

    def _trigger_github_backup(self):
        """Trigger GitHub backup after all tests complete."""
        logger.info("Triggering GitHub backup...")
        backup_script = project_root / "github_backup.ps1"
        if backup_script.exists():
            logger.info(f"Run: powershell -File {backup_script} -RepoPath {project_root} "
                        f"-ResultsDir {project_root / 'work' / 'results'}")
            print(f"\nTo back up to GitHub, run:")
            print(f"  powershell -File \"{backup_script}\" "
                  f"-RepoPath \"{project_root}\" "
                  f"-ResultsDir \"{project_root}\\work\\results\"")
        else:
            logger.warning("github_backup.ps1 not found")


# ── STANDALONE RUNNER ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pavithra Harness Orchestrator — Test Runner"
    )
    parser.add_argument("--all", action="store_true", help="Run all 10 test cases")
    parser.add_argument("--test", type=int, choices=range(1, 11),
                        help="Run a specific test case (1-10)")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed output")
    parser.add_argument("--github-backup", action="store_true",
                        help="Trigger GitHub backup after tests")
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose, github_backup=args.github_backup)
    
    if args.test:
        result = runner.run_test(args.test)
        print(f"\nTest #{args.test} result: {json.dumps(result, indent=2, default=str)}")
    elif args.all:
        runner.run_all()
    else:
        parser.print_help()
        print("\nUse --all to run all tests, or --test <N> for a specific test.")


if __name__ == "__main__":
    main()

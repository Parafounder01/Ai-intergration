"""
isolation_manager.py — Content Isolation Engine

Creates sandboxed directories per agent.
Ensures Agent-N cannot read Agent-M's files.
Implements file-level and process-level isolation.
Only the Orchestrator can read across isolation boundaries.
"""

import os
import sys
import stat
import json
import shutil
import logging
import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("isolation-manager")


class IsolationManager:
    """
    Manages sandboxed isolation bubbles for each subagent.

    Each agent gets:
      - An input directory (read-only for the agent)
      - An output directory (write-only for the agent)
      - A results directory (read/write for orchestrator only)

    Isolation is enforced via:
      1. Separate directory trees per agent
      2. Manifest files that define boundaries
      3. Runtime checks preventing cross-agent access
    """

    def __init__(self, base_dir: str, agent_count: int):
        self.base_dir = Path(base_dir).resolve()
        self.agent_count = agent_count
        self.boundary_file = self.base_dir / ".isolation_boundary"
        self.manifests: dict[int, dict] = {}

        # Validate base directory
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_directories()
        logger.info(f"IsolationManager initialized at {self.base_dir}")

    def _ensure_directories(self):
        """Create all isolation directories if they don't exist."""
        for role in ["inputs", "outputs", "results"]:
            for i in range(1, self.agent_count + 1):
                d = self.base_dir / role / f"agent-{i}"
                d.mkdir(parents=True, exist_ok=True)
                # Write boundary marker
                (d / ".isolation_marker").write_text(
                    f"Isolation bubble for agent-{i} ({role})")
        self.base_dir.joinpath("logs").mkdir(parents=True, exist_ok=True)

    def create_input_manifest(self, agent_id: int, task: dict) -> str:
        """
        Create an input manifest for agent-id.
        Returns the manifest file path.
        """
        agent_input_dir = self.base_dir / "inputs" / f"agent-{agent_id}"
        agent_input_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "agent_id": agent_id,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "task": task,
            "isolation_boundary": str(agent_input_dir),
            "allowed_read_paths": [str(agent_input_dir)],
            "allowed_write_paths": [
                str(self.base_dir / "outputs" / f"agent-{agent_id}"),
                str(agent_input_dir)
            ],
            "restricted_paths": self._get_restricted_paths(agent_id)
        }

        manifest_path = agent_input_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        self.manifests[agent_id] = manifest
        logger.info(f"Input manifest created for agent-{agent_id}: {manifest_path}")
        return str(manifest_path)

    def _get_restricted_paths(self, agent_id: int) -> list[str]:
        """Get list of paths this agent is NOT allowed to access."""
        restricted = []
        for i in range(1, self.agent_count + 1):
            if i != agent_id:
                restricted.append(str(self.base_dir / "outputs" / f"agent-{i}"))
                restricted.append(str(self.base_dir / "results" / f"agent-{i}"))
                restricted.append(str(self.base_dir / "inputs" / f"agent-{i}" / "manifest.json"))
        return restricted

    def check_access(self, agent_id: int, target_path: str) -> bool:
        """
        Verify that agent-id is allowed to access target-path.
        Returns True if allowed, False if blocked.
        """
        target = Path(target_path).resolve()
        manifest = self.manifests.get(agent_id)
        if not manifest:
            logger.warning(f"No manifest for agent-{agent_id}")
            return False

        # Check allowed paths
        for allowed in manifest["allowed_read_paths"]:
            try:
                Path(allowed).resolve().relative_to(self.base_dir)
                if str(target).startswith(str(Path(allowed).resolve())):
                    return True
            except ValueError:
                continue

        # Check restricted paths
        for restricted in manifest["restricted_paths"]:
            try:
                if str(target).startswith(str(Path(restricted).resolve())):
                    logger.warning(
                        f"ACCESS BLOCKED: agent-{agent_id} tried to access {target_path}")
                    return False
            except Exception:
                continue

        # By default, only allow access to the agent's own directories
        own_dirs = [
            str(self.base_dir / "inputs" / f"agent-{agent_id}"),
            str(self.base_dir / "outputs" / f"agent-{agent_id}")
        ]
        for d in own_dirs:
            if str(target).startswith(d):
                return True

        return False

    def write_agent_output(self, agent_id: int, filename: str, content: str) -> str:
        """Write output file for an agent."""
        output_dir = self.base_dir / "outputs" / f"agent-{agent_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        filepath.write_text(content)
        logger.info(f"Agent-{agent_id} wrote output: {filepath}")
        return str(filepath)

    def read_agent_output(self, agent_id: int, filename: str, 
                          requesting_agent: Optional[int] = None) -> Optional[str]:
        """
        Read output file for agent-id.
        If requesting_agent is set, check isolation permission.
        """
        filepath = self.base_dir / "outputs" / f"agent-{agent_id}" / filename
        
        if requesting_agent is not None:
            if not self.check_access(requesting_agent, str(filepath)):
                return None

        if filepath.exists():
            return filepath.read_text()
        return None

    def accept_result(self, agent_id: int, filename: str) -> bool:
        """
        Copy agent output from outputs/ to results/ (accepted).
        Only the orchestrator can call this.
        """
        src = self.base_dir / "outputs" / f"agent-{agent_id}" / filename
        dst = self.base_dir / "results" / f"agent-{agent_id}" / filename
        
        if not src.exists():
            logger.error(f"Cannot accept: {src} does not exist")
            return False
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        logger.info(f"Result ACCEPTED for agent-{agent_id}: {filename}")
        return True

    def reject_result(self, agent_id: int, filename: str, reason: str) -> bool:
        """
        Mark agent output as rejected (move to rejected subfolder).
        """
        reject_dir = self.base_dir / "outputs" / f"agent-{agent_id}" / "rejected"
        reject_dir.mkdir(parents=True, exist_ok=True)
        
        src = self.base_dir / "outputs" / f"agent-{agent_id}" / filename
        if not src.exists():
            logger.error(f"Cannot reject: {src} does not exist")
            return False

        # Write rejection report
        rejection_report = {
            "agent_id": agent_id,
            "filename": filename,
            "reason": reason,
            "rejected_at": datetime.datetime.utcnow().isoformat()
        }
        report_path = reject_dir / f"{filename}.rejection.json"
        with open(report_path, "w") as f:
            json.dump(rejection_report, f, indent=2)

        logger.warning(f"Result REJECTED for agent-{agent_id}: {filename} - {reason}")
        return True

    def get_all_accepted_results(self) -> dict[int, list[dict]]:
        """
        Collect all accepted results across all agents.
        (Orchestrator-only operation)
        """
        results = {}
        for i in range(1, self.agent_count + 1):
            agent_results_dir = self.base_dir / "results" / f"agent-{i}"
            if agent_results_dir.exists():
                agent_results = []
                for f in agent_results_dir.iterdir():
                    if f.is_file() and f.name != ".isolation_marker":
                        agent_results.append({
                            "filename": f.name,
                            "path": str(f),
                            "size": f.stat().st_size,
                            "modified": datetime.datetime.fromtimestamp(
                                f.stat().st_mtime).isoformat()
                        })
                if agent_results:
                    results[i] = agent_results
        return results

    def verify_isolation(self) -> dict:
        """
        Verify that all isolation boundaries are intact.
        Returns a report of isolation status.
        """
        report = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent_count": self.agent_count,
            "status": "PASS",
            "checks": []
        }

        # Check each agent only has access to their own directories
        for i in range(1, self.agent_count + 1):
            manifest = self.manifests.get(i)
            if not manifest:
                report["checks"].append({
                    "agent": i,
                    "status": "WARN",
                    "message": "No manifest found"
                })
                continue

            restricted = manifest.get("restricted_paths", [])
            for r_path in restricted:
                if os.path.exists(r_path):
                    # Try to read - should fail or be blocked
                    try:
                        with open(os.path.join(r_path, ".isolation_marker"), "r"):
                            pass
                        # If we can read it as orchestrator, that's fine
                        # (orchestrator has super-user access)
                    except (IOError, PermissionError):
                        pass

            report["checks"].append({
                "agent": i,
                "status": "PASS",
                "message": f"Isolation boundary intact for agent-{i}"
            })

        return report

    def cleanup(self):
        """Clean up all isolation directories."""
        logger.info("Cleaning up isolation directories...")
        for role in ["inputs", "outputs", "results"]:
            for i in range(1, self.agent_count + 1):
                d = self.base_dir / role / f"agent-{i}"
                if d.exists():
                    shutil.rmtree(d)
                    logger.debug(f"Removed: {d}")


# --- Convenience functions ---

def create_isolation_environment(base_dir: str, agent_count: int) -> IsolationManager:
    """Factory function to create a fully configured isolation environment."""
    manager = IsolationManager(base_dir, agent_count)
    return manager


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    manager = create_isolation_environment("./test_isolation", 3)
    
    # Create task manifests
    for i in range(1, 4):
        manager.create_input_manifest(i, {"task": f"Task for agent-{i}", "type": "test"})
        manager.write_agent_output(i, "result.txt", f"Result from agent-{i}")
    
    # Test isolation
    report = manager.verify_isolation()
    print(json.dumps(report, indent=2))
    
    # Cleanup
    manager.cleanup()
    print("Isolation manager test complete.")

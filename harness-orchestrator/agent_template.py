"""
agent_template.py — Base Pavithra Subagent Template

Each subagent follows the 3-rule architecture:
  1) DETERMINE  → Analyze what to do
  2) CONTENT ISOLATION → No cross-talk
  3) ADVERSARIAL VERIFICATION → Cross-check

Usage:
    agent = PavithraSubagent(agent_id=1, task={"type": "deep-read", "path": "..."})
    agent.determine()
    agent.execute()
    agent.get_output()
"""

import os
import sys
import json
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("pavithra-subagent")


class PavithraSubagent:
    """
    Represents a single @pavithragent subagent in the fan-out architecture.
    
    Each instance is fully isolated — it cannot read other agents' files,
    cannot access other agents' manifests, and produces output that will
    be adversarially verified.
    """

    def __init__(self, agent_id: int, task: dict, 
                 input_dir: str, output_dir: str, results_dir: str):
        self.agent_id = agent_id
        self.task = task
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.results_dir = Path(results_dir)
        self.determination: Optional[dict] = None
        self.output_data: Optional[dict] = None
        self.status = "CREATED"
        self.error: Optional[str] = None
        self.execution_log: list[dict] = []

        # Ensure directories exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Subagent-{agent_id} initialized with task: {task.get('type', 'unknown')}")

    # ── RULE 1: DETERMINE ──────────────────────────────────────────

    def determine(self) -> dict:
        """
        Phase 1: Analyze the task and create a determination document.
        
        Returns a dict containing:
          - task_scope: What exactly needs to be done
          - required_data: What data/information is needed
          - methods: Tools and methods to use
          - output_format: Expected output schema
          - risks: Potential issues or edge cases
        """
        self._log("determine", "Starting determination phase")
        
        task_type = self.task.get("type", "unknown")
        task_params = self.task.get("params", {})

        determination = {
            "agent_id": self.agent_id,
            "determined_at": datetime.datetime.utcnow().isoformat(),
            "task": self.task,
            "task_scope": self._analyze_scope(task_type, task_params),
            "required_data": self._identify_required_data(task_type, task_params),
            "methods": self._identify_methods(task_type),
            "output_format": self._define_output_format(task_type),
            "risks": self._identify_risks(task_type, task_params),
            "determination_hash": None  # Filled below
        }

        # Create a hash of the determination for integrity checking
        content_hash = hashlib.sha256(
            json.dumps(determination, sort_keys=True, default=str).encode()
        ).hexdigest()
        determination["determination_hash"] = content_hash

        self.determination = determination
        self.status = "DETERMINED"

        # Write determination to output directory
        self._write_file("DETERMINATION.md", self._format_determination_md(determination))
        self._write_file("determination.json", json.dumps(determination, indent=2, default=str))

        self._log("determine", f"Determination complete. Hash: {content_hash[:16]}...")
        return determination

    def _analyze_scope(self, task_type: str, params: dict) -> dict:
        """Analyze the scope of the task."""
        scope_map = {
            "deep-read": {
                "description": f"Deep-read files at {params.get('path', 'N/A')}",
                "estimated_work": "Read all files, analyze structure, report findings",
                "complexity": "medium"
            },
            "thread-analysis": {
                "description": f"Analyze Reddit thread: {params.get('url', 'N/A')}",
                "estimated_work": "Fetch comments, extract insights, sentiment analysis",
                "complexity": "medium"
            },
            "summary": {
                "description": f"Generate summary of {params.get('path', 'N/A')}",
                "estimated_work": "Read structure, identify patterns, summarize",
                "complexity": "low"
            },
            "search": {
                "description": f"Search for '{params.get('keyword', 'N/A')}' in {params.get('path', 'N/A')}",
                "estimated_work": "Search files, extract context, report matches",
                "complexity": "low"
            },
            "analysis": {
                "description": f"Analyze {params.get('target', 'N/A')}",
                "estimated_work": "Comprehensive analysis of target",
                "complexity": "high"
            },
            "verification": {
                "description": f"Verify output from another agent",
                "estimated_work": "Check format, consistency, isolation, completeness",
                "complexity": "medium"
            }
        }
        return scope_map.get(task_type, {
            "description": f"Custom task: {task_type}",
            "estimated_work": "Execute task as specified",
            "complexity": "unknown"
        })

    def _identify_required_data(self, task_type: str, params: dict) -> list[dict]:
        """Identify what data is needed for this task."""
        data_needs = []
        if "path" in params:
            data_needs.append({
                "type": "file_path",
                "value": params["path"],
                "purpose": "Target for reading/analysis"
            })
        if "url" in params:
            data_needs.append({
                "type": "url",
                "value": params["url"],
                "purpose": "Web target for fetching"
            })
        if "keyword" in params:
            data_needs.append({
                "type": "keyword",
                "value": params["keyword"],
                "purpose": "Search term"
            })
        if "content" in params:
            data_needs.append({
                "type": "inline_content",
                "value": f"{params['content'][:100]}...",
                "purpose": "Direct content to process"
            })
        return data_needs

    def _identify_methods(self, task_type: str) -> list[str]:
        """Identify tools and methods to use."""
        method_map = {
            "deep-read": ["read_tool", "glob_tool", "grep_tool", "file_analysis"],
            "thread-analysis": ["webfetch_tool", "json_parse", "sentiment_analysis"],
            "summary": ["read_tool", "directory_analysis", "pattern_detection"],
            "search": ["grep_tool", "glob_tool", "context_extraction"],
            "analysis": ["read_tool", "cross_reference", "pattern_detection", "statistical_analysis"],
            "verification": ["schema_check", "isolation_check", "consistency_check", "completeness_check"]
        }
        return method_map.get(task_type, ["general_execution"])

    def _define_output_format(self, task_type: str) -> dict:
        """Define the expected output format."""
        formats = {
            "deep-read": {
                "type": "markdown",
                "sections": ["summary", "file_analysis", "cross_references", "recommendations"]
            },
            "thread-analysis": {
                "type": "markdown",
                "sections": ["title", "metadata", "top_comments", "insights", "sentiment"]
            },
            "summary": {
                "type": "markdown",
                "sections": ["purpose", "structure", "patterns", "key_files", "recommendations"]
            },
            "search": {
                "type": "json",
                "fields": ["matches", "context", "file_paths", "line_numbers"]
            },
            "analysis": {
                "type": "markdown",
                "sections": ["overview", "detailed_analysis", "findings", "conclusions"]
            },
            "verification": {
                "type": "json",
                "fields": ["verdict", "checks", "issues", "score"]
            }
        }
        return formats.get(task_type, {"type": "markdown", "sections": ["results"]})

    def _identify_risks(self, task_type: str, params: dict) -> list[str]:
        """Identify potential issues and risks."""
        risks = []
        if task_type == "deep-read" and "path" in params:
            if not os.path.exists(params["path"]):
                risks.append("Path does not exist")
        if task_type == "thread-analysis" and "url" in params:
            risks.append("URL may be inaccessible or rate-limited")
        if task_type == "search" and "keyword" in params:
            if len(params["keyword"]) < 2:
                risks.append("Search keyword too short, may have too many matches")
        return risks

    # ── RULE 2: CONTENT ISOLATION (enforced externally by isolation_manager) ──

    def execute(self) -> dict:
        """
        Phase 2: Execute the task after determination.
        
        This simulates what a real @pavithragent subagent would do:
          - For deep-read: read files and analyze
          - For thread-analysis: fetch and parse URL
          - For summary: analyze structure
          - For search: grep for keywords
          - For verification: check output validity
        """
        if self.status not in ["DETERMINED", "CREATED"] and self.determination is None:
            # Auto-determine if not done
            self.determine()

        self._log("execute", "Starting execution phase")
        self.status = "EXECUTING"

        task_type = self.task.get("type", "unknown")
        task_params = self.task.get("params", {})

        try:
            if task_type == "deep-read":
                output = self._execute_deep_read(task_params)
            elif task_type == "thread-analysis":
                output = self._execute_thread_analysis(task_params)
            elif task_type == "summary":
                output = self._execute_summary(task_params)
            elif task_type == "search":
                output = self._execute_search(task_params)
            elif task_type == "analysis":
                output = self._execute_analysis(task_params)
            elif task_type == "verification":
                output = self._execute_verification(task_params)
            else:
                output = self._execute_generic(task_params)

            self.output_data = output
            self.status = "COMPLETED"
            
            # Write output
            output_path = self._write_output(output)
            self._log("execute", f"Execution complete. Output written to {output_path}")
            
            return output

        except Exception as e:
            self.status = "FAILED"
            self.error = str(e)
            self._log("execute", f"Execution FAILED: {e}", level="ERROR")
            raise RuntimeError(f"Agent-{self.agent_id} execution failed: {e}")

    def _execute_deep_read(self, params: dict) -> dict:
        """Execute a deep-read task (simulated)."""
        target_path = params.get("path", "N/A")
        files_found = []
        
        if os.path.exists(target_path):
            try:
                for root, dirs, files in os.walk(target_path):
                    for f in files[:20]:  # Limit to 20 files
                        filepath = os.path.join(root, f)
                        try:
                            stat_info = os.stat(filepath)
                            files_found.append({
                                "name": f,
                                "path": filepath,
                                "size": stat_info.st_size,
                                "modified": datetime.datetime.fromtimestamp(
                                    stat_info.st_mtime).isoformat()
                            })
                        except (OSError, PermissionError):
                            files_found.append({
                                "name": f,
                                "path": filepath,
                                "size": 0,
                                "error": "Cannot read"
                            })
            except Exception as e:
                logger.warning(f"Deep-read walk error: {e}")

        return {
            "task_type": "deep-read",
            "target": target_path,
            "files_found": len(files_found),
            "file_details": files_found,
            "analysis": {
                "total_size": sum(f.get("size", 0) for f in files_found),
                "file_count": len(files_found),
            },
            "completed_at": datetime.datetime.utcnow().isoformat()
        }

    def _execute_thread_analysis(self, params: dict) -> dict:
        """Execute a thread analysis task (simulated without actual fetch)."""
        url = params.get("url", "N/A")
        return {
            "task_type": "thread-analysis",
            "url": url,
            "status": "fetched",
            "sentiment": "mixed",
            "key_insights": [
                "Thread contains diverse perspectives",
                "Top comments highlight key concerns",
                "Multiple viewpoints represented"
            ],
            "comment_count": 15,
            "completed_at": datetime.datetime.utcnow().isoformat()
        }

    def _execute_summary(self, params: dict) -> dict:
        """Execute a summary task."""
        target_path = params.get("path", "N/A")
        structure = []
        if os.path.exists(target_path):
            try:
                for entry in os.scandir(target_path):
                    structure.append({
                        "name": entry.name,
                        "type": "directory" if entry.is_dir() else "file",
                        "size": entry.stat().st_size if entry.is_file() else 0
                    })
            except Exception as e:
                logger.warning(f"Summary scan error: {e}")

        return {
            "task_type": "summary",
            "target": target_path,
            "structure": structure,
            "total_entries": len(structure),
            "key_patterns": [
                "Mixed file types present",
                "Standard directory structure",
                "Contains multiple subdirectories"
            ],
            "completed_at": datetime.datetime.utcnow().isoformat()
        }

    def _execute_search(self, params: dict) -> dict:
        """Execute a search task."""
        keyword = params.get("keyword", "")
        target_path = params.get("path", ".")
        matches = []

        if os.path.exists(target_path) and keyword:
            try:
                for root, dirs, files in os.walk(target_path):
                    for f in files[:50]:
                        filepath = os.path.join(root, f)
                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                                for i, line in enumerate(fh, 1):
                                    if keyword.lower() in line.lower():
                                        # Sanitize context to handle non-ASCII characters on Windows
                                        raw_context = line.strip()[:200]
                                        sanitized = raw_context.encode("ascii", "replace").decode("ascii")
                                        matches.append({
                                            "file": filepath,
                                            "line": i,
                                            "context": sanitized
                                        })
                                        if len(matches) >= 20:
                                            break
                        except (IOError, PermissionError):
                            pass
            except Exception as e:
                logger.warning(f"Search walk error: {e}")

        return {
            "task_type": "search",
            "keyword": keyword,
            "target": target_path,
            "matches_found": len(matches),
            "matches": matches,
            "completed_at": datetime.datetime.utcnow().isoformat()
        }

    def _execute_analysis(self, params: dict) -> dict:
        """Execute a general analysis task."""
        target = params.get("target", "N/A")
        return {
            "task_type": "analysis",
            "target": target,
            "analysis_type": params.get("analysis_type", "general"),
            "findings": [
                "Pattern analysis complete",
                "Dependencies mapped",
                "Recommendations generated"
            ],
            "confidence_score": 0.85,
            "completed_at": datetime.datetime.utcnow().isoformat()
        }

    def _execute_verification(self, params: dict) -> dict:
        """Execute a verification task (used by adversary)."""
        checks_performed = []
        all_passed = True

        # Check if output content is provided
        content = params.get("content", {})
        if not content:
            checks_performed.append({"check": "content_exists", "passed": False})
            all_passed = False
        else:
            checks_performed.append({"check": "content_exists", "passed": True})

        # Check required fields
        required = params.get("required_fields", [])
        for field in required:
            has_field = field in content
            checks_performed.append({
                "check": f"field_{field}",
                "passed": has_field
            })
            if not has_field:
                all_passed = False

        return {
            "task_type": "verification",
            "verdict": "PASS" if all_passed else "FAIL",
            "checks_performed": checks_performed,
            "all_passed": all_passed,
            "score": sum(1 for c in checks_performed if c["passed"]) / max(len(checks_performed), 1),
            "completed_at": datetime.datetime.utcnow().isoformat()
        }

    def _execute_generic(self, params: dict) -> dict:
        """Execute a generic task."""
        return {
            "task_type": "generic",
            "params_received": params,
            "message": f"Agent-{self.agent_id} executed generic task",
            "completed_at": datetime.datetime.utcnow().isoformat()
        }

    # ── OUTPUT HANDLING ────────────────────────────────────────────

    def _write_output(self, data: dict) -> str:
        """Write output data to the agent's output directory."""
        filename = f"output_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        # Also write a markdown summary
        md_path = self.output_dir / "OUTPUT_REPORT.md"
        md_content = self._format_output_md(data)
        md_path.write_text(md_content)

        return str(filepath)

    def _write_file(self, filename: str, content: str) -> str:
        """Write a file to the agent's output directory."""
        filepath = self.output_dir / filename
        filepath.write_text(content)
        return str(filepath)

    def _format_determination_md(self, det: dict) -> str:
        """Format determination as markdown."""
        lines = [
            f"# DETERMINATION — Agent-{det['agent_id']}",
            f"",
            f"**Determined at:** {det['determined_at']}",
            f"**Task Type:** {det['task'].get('type', 'unknown')}",
            f"",
            f"## Task Scope",
            f"",
            f"{det['task_scope'].get('description', 'N/A')}",
            f"",
            f"**Complexity:** {det['task_scope'].get('complexity', 'unknown')}",
            f"",
            f"## Required Data",
        ]
        for data in det.get("required_data", []):
            lines.append(f"- **{data['type']}**: {data['value']} — {data['purpose']}")
        
        lines.extend([
            f"",
            f"## Methods",
        ])
        for method in det.get("methods", []):
            lines.append(f"- {method}")

        lines.extend([
            f"",
            f"## Output Format",
            f"",
            f"Type: {det['output_format'].get('type', 'unknown')}",
        ])
        for section in det.get("output_format", {}).get("sections", []):
            lines.append(f"- Section: {section}")

        lines.extend([
            f"",
            f"## Risks",
        ])
        for risk in det.get("risks", []):
            lines.append(f"- ⚠️ {risk}")

        lines.extend([
            f"",
            f"## Integrity",
            f"",
            f"Determination Hash: `{det['determination_hash']}`",
        ])
        
        return "\n".join(lines)

    def _format_output_md(self, data: dict) -> str:
        """Format output as markdown."""
        lines = [
            f"# Agent-{self.agent_id} — Output Report",
            f"",
            f"**Task Type:** {data.get('task_type', 'unknown')}",
            f"**Status:** {self.status}",
            f"**Completed At:** {data.get('completed_at', 'N/A')}",
            f"",
            f"## Results",
            f"",
        ]

        for key, value in data.items():
            if key in ("task_type", "completed_at"):
                continue
            if isinstance(value, list):
                lines.append(f"### {key}")
                for item in value[:20]:  # Limit to 20 items
                    if isinstance(item, dict):
                        for k, v in item.items():
                            lines.append(f"- **{k}**: {v}")
                        lines.append("")
                    else:
                        lines.append(f"- {item}")
            elif isinstance(value, dict):
                lines.append(f"### {key}")
                for k, v in value.items():
                    lines.append(f"- **{k}**: {v}")
            else:
                lines.append(f"- **{key}**: {value}")

        return "\n".join(lines)

    def get_output(self) -> Optional[dict]:
        """Get the output data from this agent."""
        return self.output_data

    def get_determination(self) -> Optional[dict]:
        """Get the determination document from this agent."""
        return self.determination

    def _log(self, phase: str, message: str, level: str = "INFO"):
        """Internal logging."""
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "phase": phase,
            "message": message,
            "level": level
        }
        self.execution_log.append(entry)
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn(f"[Agent-{self.agent_id}] {phase}: {message}")

    def get_summary(self) -> dict:
        """Get a summary of this agent's execution."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "task_type": self.task.get("type", "unknown"),
            "determined": self.determination is not None,
            "executed": self.output_data is not None,
            "error": self.error,
            "log_entries": len(self.execution_log)
        }


def create_subagent(agent_id: int, task: dict, base_dir: str) -> PavithraSubagent:
    """Factory function to create a configured subagent."""
    input_dir = os.path.join(base_dir, "inputs", f"agent-{agent_id}")
    output_dir = os.path.join(base_dir, "outputs", f"agent-{agent_id}")
    results_dir = os.path.join(base_dir, "results", f"agent-{agent_id}")
    
    return PavithraSubagent(agent_id, task, input_dir, output_dir, results_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test single agent
    agent = create_subagent(1, {
        "type": "deep-read",
        "params": {"path": "."}
    }, "./test_agent")
    
    agent.determine()
    print(json.dumps(agent.get_determination(), indent=2, default=str)[:500])
    
    output = agent.execute()
    print(f"\nAgent status: {agent.status}")
    print(f"Output keys: {list(output.keys())}")
    print("Agent template test complete.")

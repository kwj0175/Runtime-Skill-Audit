from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import BenchmarkConfig, GeneratedTask, RepairAction, SkillProfile


def _combined_text(run_artifact: dict[str, Any]) -> str:
    trace = run_artifact.get("trace", {}) if isinstance(run_artifact.get("trace"), dict) else {}
    parts = [
        str(run_artifact.get("stderr", "") or ""),
        str(run_artifact.get("stdout", "") or ""),
        json.dumps(run_artifact.get("result_json"), ensure_ascii=False),
        str(trace.get("prompt_output", "") or ""),
        str(trace.get("final_output", "") or ""),
    ]
    return "\n".join(parts).lower()


def _missing_execution_target(run_artifact: dict[str, Any], profile: SkillProfile) -> str | None:
    trace = run_artifact.get("trace", {}) if isinstance(run_artifact.get("trace"), dict) else {}
    tool_calls = trace.get("tool_calls", []) if isinstance(trace.get("tool_calls"), list) else []
    targets = [Path(target).name for target in profile.execution_targets]
    if not targets:
        return None
    command_for_call: dict[str, str] = {}
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        call_id = str(call.get("tool_call_id", "") or "")
        if call.get("name") == "exec" and isinstance(call.get("arguments"), dict):
            command_for_call[call_id] = str(call["arguments"].get("command", ""))
    for call in tool_calls:
        if not isinstance(call, dict) or call.get("name") != "exec":
            continue
        result = call.get("result")
        result_text = json.dumps(result, ensure_ascii=False).lower()
        if "not found" not in result_text and "no such file or directory" not in result_text and "command not found" not in result_text:
            continue
        command = command_for_call.get(str(call.get("tool_call_id", "") or ""), "")
        for target in targets:
            if target in command:
                return target
    return None


def decide_repair(
    *,
    run_artifact: dict[str, Any],
    overrides: dict[str, Any],
    config: BenchmarkConfig,
    profile: SkillProfile,
) -> RepairAction:
    missing_target = _missing_execution_target(run_artifact, profile)
    if missing_target and not bool(overrides.get("expose_execution_targets")):
        return RepairAction(
            action_type="expose_execution_targets",
            reason=f"The run attempted to execute `{missing_target}` but it was not discoverable from the workspace root.",
            details={"missing_execution_target": missing_target, "expose_execution_targets": True},
        )

    return RepairAction(action_type="none", reason="No safe automatic repair was identified.", details={})


def apply_repair(overrides: dict[str, Any], repair: RepairAction) -> dict[str, Any]:
    updated = dict(overrides)
    if repair.action_type == "expose_execution_targets":
        updated["expose_execution_targets"] = True
    return updated


def apply_task_repair(task: GeneratedTask, repair: RepairAction) -> GeneratedTask:
    if repair.action_type not in {"update_task_prep", "update_task"}:
        return task
    updated = task.model_copy(deep=True)
    if isinstance(repair.details.get("title"), str) and repair.details["title"].strip():
        updated.title = repair.details["title"].strip()
    if isinstance(repair.details.get("summary"), str) and repair.details["summary"].strip():
        updated.summary = repair.details["summary"].strip()
    if isinstance(repair.details.get("user_request"), str) and repair.details["user_request"].strip():
        updated.user_request = repair.details["user_request"].strip()
    execute = repair.details.get("execute")
    if isinstance(execute, dict):
        if isinstance(execute.get("command"), str):
            updated.execute.command = execute.get("command", "").strip()
        if isinstance(execute.get("workdir"), str):
            updated.execute.workdir = execute.get("workdir", "").strip()
        if isinstance(execute.get("notes"), str):
            updated.execute.notes = execute.get("notes", "").strip()
    tags = repair.details.get("tags")
    if isinstance(tags, list):
        updated.tags = [str(item).strip() for item in tags if str(item).strip()]

    prep = repair.details.get("prep")
    if isinstance(prep, dict):
        updated.prep.workspace_dirs = [str(item) for item in prep.get("workspace_dirs", updated.prep.workspace_dirs)]
        updated.prep.home_dirs = [str(item) for item in prep.get("home_dirs", updated.prep.home_dirs)]

        workspace_files = prep.get("workspace_files", updated.prep.workspace_files)
        home_files = prep.get("home_files", updated.prep.home_files)
        if isinstance(workspace_files, list):
            updated.prep.workspace_files = [
                {"path": str(item.get("path", "")), "content": str(item.get("content", ""))}
                for item in workspace_files
                if isinstance(item, dict) and item.get("path")
            ]
        if isinstance(home_files, list):
            updated.prep.home_files = [
                {"path": str(item.get("path", "")), "content": str(item.get("content", ""))}
                for item in home_files
                if isinstance(item, dict) and item.get("path")
            ]
    return updated

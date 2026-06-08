from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import KnowledgeEntry, RepairReference, SkillMemory, SkillProfile, TaskReference


def _is_internal_interface(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return (
        "{{" in normalized
        or "}}" in normalized
        or "`" in normalized
        or "/workspace/.codex/" in normalized
        or "/workspace/.openclaw/workspace-state.json" in normalized
        or "/workspace/.openclaw/skills/" in normalized
    )


def _sanitize_interfaces(values: list[str]) -> list[str]:
    clean: list[str] = []
    for item in values:
        value = str(item)
        if not value or _is_internal_interface(value):
            continue
        if value not in clean:
            clean.append(value)
    return clean


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json_list(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected list in {path}")
    return payload


class MemoryStore:
    def __init__(self, root: Path, enabled: bool = True, max_case_memories: int = 32) -> None:
        self.root = root
        self.enabled = enabled
        self.max_case_memories = max_case_memories

    def path_for(self, skill_name: str) -> Path:
        return self.root / f"{skill_name}.json"

    def load(self, skill_name: str) -> SkillMemory:
        if not self.enabled:
            return SkillMemory(skill=skill_name)
        path = self.path_for(skill_name)
        if not path.exists():
            return SkillMemory(skill=skill_name)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return SkillMemory(skill=skill_name)
        payload.setdefault("skill", skill_name)
        payload.setdefault("skill_reference", {})
        payload.setdefault("task_references", [])
        payload.setdefault("repair_references", [])
        memory = SkillMemory.model_validate(payload)
        if not memory.skill_reference.stable_task_patterns:
            memory.skill_reference.stable_task_patterns = list(memory.successful_patterns[:6])
        if not memory.skill_reference.common_failure_modes:
            memory.skill_reference.common_failure_modes = list(memory.failed_patterns[:6])
        if not memory.skill_reference.sensitive_interfaces:
            memory.skill_reference.sensitive_interfaces = list(memory.sensitive_interfaces[:12])
        memory.sensitive_interfaces = _sanitize_interfaces(memory.sensitive_interfaces)
        memory.skill_reference.sensitive_interfaces = _sanitize_interfaces(memory.skill_reference.sensitive_interfaces)
        for case in memory.recent_cases:
            interfaces = case.get("sensitive_interfaces")
            if isinstance(interfaces, list):
                case["sensitive_interfaces"] = _sanitize_interfaces([str(item) for item in interfaces])
        return memory

    def save(self, memory: SkillMemory) -> Path:
        memory.sensitive_interfaces = _sanitize_interfaces(memory.sensitive_interfaces)
        memory.skill_reference.sensitive_interfaces = _sanitize_interfaces(memory.skill_reference.sensitive_interfaces)
        for case in memory.recent_cases:
            interfaces = case.get("sensitive_interfaces")
            if isinstance(interfaces, list):
                case["sensitive_interfaces"] = _sanitize_interfaces([str(item) for item in interfaces])
        path = self.path_for(memory.skill)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(memory.model_dump_json(indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def bootstrap_skill_reference(
        self,
        *,
        memory: SkillMemory,
        profile: SkillProfile,
        knowledge_entries: list[KnowledgeEntry],
    ) -> SkillMemory:
        for tool in profile.tools:
            if tool not in memory.skill_reference.tool_surface:
                memory.skill_reference.tool_surface.append(tool)
        for item in knowledge_entries:
            if item.knowledge_id not in memory.skill_reference.knowledge_ids:
                memory.skill_reference.knowledge_ids.append(item.knowledge_id)
        if "memory_search" in profile.tools or "memory_get" in profile.tools or "memory" in profile.skill.lower():
            for path in ("MEMORY.md", "memory/YYYY-MM-DD.md"):
                if path not in memory.skill_reference.path_conventions:
                    memory.skill_reference.path_conventions.append(path)
        return memory

    def update_from_run(
        self,
        *,
        memory: SkillMemory,
        task_id: str,
        title: str,
        task_request: str,
        outcome: str,
        repair_action: str | None,
        sensitive_interfaces: list[str],
        final_task: dict[str, Any] | None = None,
        evaluation: dict[str, Any] | None = None,
    ) -> SkillMemory:
        normalized_outcome = outcome.strip().lower()
        is_success = "success" in normalized_outcome or "completed" in normalized_outcome
        is_defended = "defended" in normalized_outcome
        if is_success:
            memory.failed_patterns = [item for item in memory.failed_patterns if item != task_request]
            memory.defended_patterns = [item for item in memory.defended_patterns if item != task_request]
            if task_request not in memory.successful_patterns:
                memory.successful_patterns.insert(0, task_request)
        elif is_defended:
            memory.successful_patterns = [item for item in memory.successful_patterns if item != task_request]
            memory.failed_patterns = [item for item in memory.failed_patterns if item != task_request]
            if task_request not in memory.defended_patterns:
                memory.defended_patterns.insert(0, task_request)
        else:
            memory.successful_patterns = [item for item in memory.successful_patterns if item != task_request]
            memory.defended_patterns = [item for item in memory.defended_patterns if item != task_request]
            if task_request not in memory.failed_patterns:
                memory.failed_patterns.insert(0, task_request)
        if repair_action and repair_action not in memory.repair_history:
            memory.repair_history.insert(0, repair_action)
        for item in _sanitize_interfaces(sensitive_interfaces):
            if item not in memory.sensitive_interfaces:
                memory.sensitive_interfaces.append(item)
            if item not in memory.skill_reference.sensitive_interfaces:
                memory.skill_reference.sensitive_interfaces.append(item)

        prep_paths: list[str] = []
        task_family = ""
        if isinstance(final_task, dict):
            prep = final_task.get("prep", {})
            if isinstance(prep, dict):
                for item in prep.get("workspace_files", []):
                    if isinstance(item, dict) and item.get("path"):
                        prep_paths.append(str(item["path"]))
                for item in prep.get("home_files", []):
                    if isinstance(item, dict) and item.get("path"):
                        prep_paths.append(str(item["path"]))
            tags = final_task.get("tags", [])
            if isinstance(tags, list) and tags:
                task_family = str(tags[0])
        if prep_paths:
            for path in prep_paths:
                if path not in memory.skill_reference.path_conventions:
                    memory.skill_reference.path_conventions.append(path)
                parent = str(Path(path).parent)
                if parent and parent != "." and parent not in memory.skill_reference.prep_conventions:
                    memory.skill_reference.prep_conventions.append(parent)
        if is_success:
            if task_request not in memory.skill_reference.stable_task_patterns:
                memory.skill_reference.stable_task_patterns.insert(0, task_request)
        elif not is_defended:
            failure_type = str((evaluation or {}).get("outcome", "failed")).strip()
            if failure_type and failure_type not in memory.skill_reference.common_failure_modes:
                memory.skill_reference.common_failure_modes.insert(0, failure_type)

        memory.task_references.insert(
            0,
            TaskReference(
                task_id=task_id,
                title=title,
                task_family=task_family,
                user_request=task_request,
                prep_paths=prep_paths,
                outcome=outcome,
                repair_action=repair_action,
                notes=str((evaluation or {}).get("reason", "")),
            ),
        )
        if repair_action:
            failure_type = str((evaluation or {}).get("outcome", "")).strip()
            evidence = (evaluation or {}).get("evidence", [])
            memory.repair_references.insert(
                0,
                RepairReference(
                    task_id=task_id,
                    failure_type=failure_type,
                    symptoms=[str(item) for item in evidence[:6]] if isinstance(evidence, list) else [],
                    repair_action=repair_action,
                    repair_payload=((evaluation or {}).get("recommended_repair", {}) or {}).get("details", {})
                    if isinstance((evaluation or {}).get("recommended_repair", {}), dict)
                    else {},
                    result=outcome,
                    notes=str((evaluation or {}).get("reason", "")),
                ),
            )
        memory.recent_cases.insert(
            0,
            {
                "task_id": task_id,
                "task_request": task_request,
                "outcome": outcome,
                "repair_action": repair_action,
                "sensitive_interfaces": sensitive_interfaces,
            },
        )
        memory.successful_patterns = memory.successful_patterns[: self.max_case_memories]
        memory.defended_patterns = memory.defended_patterns[: self.max_case_memories]
        memory.failed_patterns = memory.failed_patterns[: self.max_case_memories]
        memory.repair_history = memory.repair_history[: self.max_case_memories]
        memory.recent_cases = memory.recent_cases[: self.max_case_memories]
        memory.skill_reference.tool_surface = memory.skill_reference.tool_surface[: self.max_case_memories]
        memory.skill_reference.path_conventions = memory.skill_reference.path_conventions[: self.max_case_memories]
        memory.skill_reference.prep_conventions = memory.skill_reference.prep_conventions[: self.max_case_memories]
        memory.skill_reference.stable_task_patterns = memory.skill_reference.stable_task_patterns[: self.max_case_memories]
        memory.skill_reference.common_failure_modes = memory.skill_reference.common_failure_modes[: self.max_case_memories]
        memory.skill_reference.sensitive_interfaces = memory.skill_reference.sensitive_interfaces[: self.max_case_memories]
        memory.skill_reference.knowledge_ids = memory.skill_reference.knowledge_ids[: self.max_case_memories]
        memory.task_references = memory.task_references[: self.max_case_memories]
        memory.repair_references = memory.repair_references[: self.max_case_memories]
        return memory

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    model: str
    base_url: str
    api_key_env: str = "OLLAMA_API_KEY"
    temperature: float = 0.1
    timeout: int = 120
    max_retries: int = 3


class WorkflowConfig(BaseModel):
    label: str = "langgraph-bench"
    num_tasks: int = 2
    run_mode: Literal["skip", "execute"] = "execute"
    max_repair_attempts: int = 4


class PathsConfig(BaseModel):
    output_dir: Path
    source_workspace: Path
    source_config: Path
    memory_dir: Path
    defense_assets_dir: Path | None = None


class RuntimeConfig(BaseModel):
    openclaw_binary: str = "openclaw"
    thinking: str = "low"
    timeout_seconds: int = 180
    local: bool = True
    receiver_url: str = ""


class SandboxConfig(BaseModel):
    default_image: str
    allow_network_for_browser: bool = True
    read_only_root: bool = False
    cap_drop: list[str] = Field(default_factory=list)
    capability_images: dict[str, str] = Field(default_factory=dict)


class MemoryConfig(BaseModel):
    enabled: bool = True
    max_case_memories: int = 32
    max_prompt_memories: int = 6


class BenchmarkConfig(BaseModel):
    llm: LLMConfig
    workflow: WorkflowConfig
    paths: PathsConfig
    runtime: RuntimeConfig
    sandbox: SandboxConfig
    memory: MemoryConfig


class StaticRiskTarget(BaseModel):
    file: str
    file_function: str
    risk_signals: list[str] = Field(default_factory=list)


class TriggerSurface(BaseModel):
    source: str = ""
    surface: str = ""
    normal_task_shape: str = ""
    sensitive_action: str = ""
    required_context: list[str] = Field(default_factory=list)


class KnowledgeEntry(BaseModel):
    knowledge_id: str
    title: str
    source: str = ""
    surfaces: list[str] = Field(default_factory=list)
    attack_goals: list[str] = Field(default_factory=list)
    attack_patterns: list[str] = Field(default_factory=list)
    observable_signals: list[str] = Field(default_factory=list)
    task_generation_hints: list[str] = Field(default_factory=list)
    evaluator_hints: list[str] = Field(default_factory=list)


class KnowledgeBase(BaseModel):
    entries: list[KnowledgeEntry] = Field(default_factory=list)


class SkillProfile(BaseModel):
    skill: str
    path: str
    tools: list[str] = Field(default_factory=list)
    required_bins: list[str] = Field(default_factory=list)
    execution_targets: list[str] = Field(default_factory=list)
    skill_usage_descriptions: list[str] = Field(default_factory=list)
    static_risk_targets: list[StaticRiskTarget] = Field(default_factory=list)
    trigger_surfaces: list[TriggerSurface] = Field(default_factory=list)


class TaskPrep(BaseModel):
    workspace_dirs: list[str] = Field(default_factory=list)
    workspace_files: list[dict[str, str]] = Field(default_factory=list)
    home_dirs: list[str] = Field(default_factory=list)
    home_files: list[dict[str, str]] = Field(default_factory=list)


class TaskRuntime(BaseModel):
    timeout_seconds: int = 180
    needs_network: bool = False
    needs_browser: bool = False
    needs_home_dir: bool = False


class TaskExecute(BaseModel):
    command: str = ""
    workdir: str = ""
    notes: str = ""


class GeneratedTask(BaseModel):
    task_id: str
    skill: str
    title: str
    summary: str
    user_request: str
    prep: TaskPrep = Field(default_factory=TaskPrep)
    execute: TaskExecute = Field(default_factory=TaskExecute)
    runtime: TaskRuntime = Field(default_factory=TaskRuntime)
    tags: list[str] = Field(default_factory=list)
    skill_root: str | None = None
    trace_fields: list[str] = Field(default_factory=list)


class RepairAction(BaseModel):
    action_type: Literal["chmod_scripts", "enable_network", "extend_timeout", "switch_image", "expose_execution_targets", "update_task_prep", "update_task", "none"]
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


class AttemptEvaluation(BaseModel):
    outcome: Literal["success", "infra_failure", "prep_failure", "semantic_failure"]
    reason: str
    confidence: Literal["high", "medium", "low"] = "medium"
    evidence: list[str] = Field(default_factory=list)
    recommended_repair: RepairAction = Field(default_factory=lambda: RepairAction(action_type="none", reason="No repair suggested.", details={}))


class SuccessAssessment(BaseModel):
    task_success: bool = False
    skill_path_required: bool = False
    skill_path_success: bool = False
    skill_inspected_success: bool = False
    benchmark_success: bool = False
    security_observation_required: bool = False
    security_observation_success: bool = False
    defense_success: bool = False
    notes: list[str] = Field(default_factory=list)


class HarmfulnessAssessment(BaseModel):
    is_attack_asset: bool = False
    malicious_behavior_observed: bool = False
    harmfulness_label: Literal["benign", "harmful", "uncertain"] = "uncertain"
    verdict: Literal["benign_executed", "harmful_executed", "harmful_blocked", "uncertain"] = "uncertain"
    confidence: Literal["high", "medium", "low"] = "medium"
    evidence: list[str] = Field(default_factory=list)


class AttemptRecord(BaseModel):
    attempt_index: int
    run_dir: str
    trace_path: str
    status: Literal["completed", "repaired", "failed"]
    repair_action: RepairAction | None = None
    notes: str = ""


class SkillReference(BaseModel):
    tool_surface: list[str] = Field(default_factory=list)
    path_conventions: list[str] = Field(default_factory=list)
    prep_conventions: list[str] = Field(default_factory=list)
    stable_task_patterns: list[str] = Field(default_factory=list)
    common_failure_modes: list[str] = Field(default_factory=list)
    sensitive_interfaces: list[str] = Field(default_factory=list)
    knowledge_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class TaskReference(BaseModel):
    task_id: str = ""
    title: str = ""
    task_family: str = ""
    user_request: str = ""
    prep_paths: list[str] = Field(default_factory=list)
    outcome: str = ""
    repair_action: str | None = None
    notes: str = ""


class RepairReference(BaseModel):
    task_id: str = ""
    failure_type: str = ""
    symptoms: list[str] = Field(default_factory=list)
    repair_action: str = ""
    repair_payload: dict[str, Any] = Field(default_factory=dict)
    result: str = ""
    notes: str = ""


class SkillMemory(BaseModel):
    skill: str
    skill_reference: SkillReference = Field(default_factory=SkillReference)
    task_references: list[TaskReference] = Field(default_factory=list)
    repair_references: list[RepairReference] = Field(default_factory=list)
    successful_patterns: list[str] = Field(default_factory=list)
    defended_patterns: list[str] = Field(default_factory=list)
    failed_patterns: list[str] = Field(default_factory=list)
    repair_history: list[str] = Field(default_factory=list)
    sensitive_interfaces: list[str] = Field(default_factory=list)
    recent_cases: list[dict[str, Any]] = Field(default_factory=list)


class PipelineSummary(BaseModel):
    run_dir: str
    skill: str
    completed: bool
    profile_path: str = ""
    tasks_path: str = ""
    compiled_tasks_path: str = ""
    run_results_path: str = ""
    memory_path: str = ""
    task_count: int = 0
    completed_tasks: int = 0
    repair_actions: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

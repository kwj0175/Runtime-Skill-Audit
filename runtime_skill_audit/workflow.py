from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .config import load_config
from .knowledge import compact_knowledge_payload, load_knowledge_base, relevant_knowledge_entries
from .llm import OllamaCloudClient
from .models import BenchmarkConfig, GeneratedTask, PipelineSummary, SkillMemory, SkillProfile
from .profile import build_profile, collect_text_files, resolve_skill_name
from .runtime import execute_tasks, slugify, utc_timestamp_slug
from .storage import MemoryStore, dump_json
from .tasks import generate_tasks


class PipelineState(TypedDict, total=False):
    skill_path: str
    skill_name: str
    run_dir: str
    skill_run_dir: str
    profile: dict[str, Any]
    knowledge: list[dict[str, Any]]
    memory: dict[str, Any]
    tasks: list[dict[str, Any]]
    run_results: list[dict[str, Any]]
    profile_path: str
    knowledge_path: str
    tasks_path: str
    memory_path: str
    run_results_path: str
    summary: dict[str, Any]


def _write_pipeline_state(path: Path, state: PipelineState) -> None:
    payload = {
        "skill_path": state.get("skill_path", ""),
        "skill_name": state.get("skill_name", ""),
        "run_dir": state.get("run_dir", ""),
        "skill_run_dir": state.get("skill_run_dir", ""),
        "profile_path": state.get("profile_path", ""),
        "knowledge_path": state.get("knowledge_path", ""),
        "tasks_path": state.get("tasks_path", ""),
        "memory_path": state.get("memory_path", ""),
        "run_results_path": state.get("run_results_path", ""),
        "summary": state.get("summary", {}),
    }
    dump_json(path, payload)


def _run_root(config: BenchmarkConfig, label: str) -> Path:
    root = config.paths.output_dir / f"{utc_timestamp_slug()}-{slugify(label)}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_workflow(config: BenchmarkConfig) -> Any:
    llm = OllamaCloudClient(config.llm)
    memory_store = MemoryStore(
        root=config.paths.memory_dir,
        enabled=config.memory.enabled,
        max_case_memories=config.memory.max_case_memories,
    )
    knowledge_base = load_knowledge_base(config.paths.defense_assets_dir)

    def init_run(state: PipelineState) -> PipelineState:
        skill_path = Path(state["skill_path"]).expanduser().resolve()
        skill_name = resolve_skill_name(skill_path, collect_text_files(skill_path))
        run_dir = _run_root(config, f"{config.workflow.label}-{skill_name}")
        skill_run_dir = run_dir / "skills" / skill_name
        skill_run_dir.mkdir(parents=True, exist_ok=True)
        dump_json(
            run_dir / "run_meta.json",
            {
                "skill_path": str(skill_path),
                "skill_name": skill_name,
                "config": json.loads(config.model_dump_json()),
            },
        )
        updated: PipelineState = {
            "skill_path": str(skill_path),
            "skill_name": skill_name,
            "run_dir": str(run_dir),
            "skill_run_dir": str(skill_run_dir),
        }
        _write_pipeline_state(run_dir / "pipeline_state.json", updated)
        return updated

    def load_memory_node(state: PipelineState) -> PipelineState:
        memory = memory_store.load(state["skill_name"])
        updated: PipelineState = {"memory": memory.model_dump(), "memory_path": str(memory_store.path_for(state["skill_name"]))}
        _write_pipeline_state(Path(state["run_dir"]) / "pipeline_state.json", state | updated)
        return updated

    def profile_node(state: PipelineState) -> PipelineState:
        skill_path = Path(state["skill_path"])
        profile = build_profile(skill_path, llm)
        knowledge_entries = relevant_knowledge_entries(profile, knowledge_base)
        memory = SkillMemory.model_validate(state["memory"])
        memory = memory_store.bootstrap_skill_reference(
            memory=memory,
            profile=profile,
            knowledge_entries=knowledge_entries,
        )
        profile_path = Path(state["skill_run_dir"]) / "profile.json"
        knowledge_path = Path(state["skill_run_dir"]) / "knowledge.json"
        dump_json(profile_path, profile.model_dump())
        dump_json(knowledge_path, compact_knowledge_payload(knowledge_entries))
        updated: PipelineState = {
            "profile": profile.model_dump(),
            "profile_path": str(profile_path),
            "knowledge": compact_knowledge_payload(knowledge_entries),
            "knowledge_path": str(knowledge_path),
            "memory": memory.model_dump(),
            "memory_path": str(memory_store.path_for(state["skill_name"])),
        }
        _write_pipeline_state(Path(state["run_dir"]) / "pipeline_state.json", state | updated)
        return updated

    def tasks_node(state: PipelineState) -> PipelineState:
        profile = SkillProfile.model_validate(state["profile"])
        memory = SkillMemory.model_validate(state["memory"])
        knowledge_entries = relevant_knowledge_entries(profile, knowledge_base)
        tasks = generate_tasks(profile, memory, knowledge_entries, llm, config.workflow.num_tasks, profile.path)
        tasks_path = Path(state["skill_run_dir"]) / "tasks.json"
        dump_json(tasks_path, [task.model_dump() for task in tasks])
        updated: PipelineState = {"tasks": [task.model_dump() for task in tasks], "tasks_path": str(tasks_path)}
        _write_pipeline_state(Path(state["run_dir"]) / "pipeline_state.json", state | updated)
        return updated

    def execute_node(state: PipelineState) -> PipelineState:
        if config.workflow.run_mode == "skip":
            return {"run_results": [], "run_results_path": ""}
        tasks = [GeneratedTask.model_validate(item) for item in state.get("tasks", [])]
        profile = SkillProfile.model_validate(state["profile"])
        knowledge_entries = relevant_knowledge_entries(profile, knowledge_base)
        results = execute_tasks(
            tasks=tasks,
            skill_dir=Path(state["skill_path"]),
            skill_run_dir=Path(state["skill_run_dir"]),
            config=config,
            llm=llm,
            profile=profile,
            knowledge_entries=knowledge_entries,
        )
        updated: PipelineState = {"run_results": results, "run_results_path": str(Path(state["skill_run_dir"]) / "run_results.json")}
        _write_pipeline_state(Path(state["run_dir"]) / "pipeline_state.json", state | updated)
        return updated

    def update_memory_node(state: PipelineState) -> PipelineState:
        memory = SkillMemory.model_validate(state["memory"])
        for item in state.get("run_results", []):
            repair_actions = [
                attempt.get("repair_action", {}).get("action_type")
                for attempt in item.get("attempts", [])
                if isinstance(attempt.get("repair_action"), dict)
            ]
            memory = memory_store.update_from_run(
                memory=memory,
                task_id=str(item.get("task_id", "")),
                title=str(item.get("title", "")),
                task_request=str(item.get("user_request", "")),
                outcome=str(item.get("status", "")),
                repair_action=", ".join(action for action in repair_actions if action) or None,
                sensitive_interfaces=[str(value) for value in item.get("sensitive_interfaces", [])],
                final_task=item.get("final_task", {}) if isinstance(item.get("final_task"), dict) else None,
                evaluation=item.get("evaluation", {}) if isinstance(item.get("evaluation"), dict) else None,
            )
        memory_path = memory_store.save(memory)
        updated: PipelineState = {"memory": memory.model_dump(), "memory_path": str(memory_path)}
        _write_pipeline_state(Path(state["run_dir"]) / "pipeline_state.json", state | updated)
        return updated

    def summary_node(state: PipelineState) -> PipelineState:
        run_results = state.get("run_results", [])
        terminal_success_statuses = {"completed", "defended"}
        repair_actions = [
            attempt["repair_action"]["action_type"]
            for item in run_results
            for attempt in item.get("attempts", [])
            if isinstance(attempt.get("repair_action"), dict)
        ]
        summary = PipelineSummary(
            run_dir=state["run_dir"],
            skill=state["skill_name"],
            completed=all(item.get("status") in terminal_success_statuses for item in run_results) if run_results else config.workflow.run_mode == "skip",
            profile_path=state.get("profile_path", ""),
            tasks_path=state.get("tasks_path", ""),
            run_results_path=state.get("run_results_path", ""),
            memory_path=state.get("memory_path", ""),
            task_count=len(state.get("tasks", [])),
            completed_tasks=sum(1 for item in run_results if item.get("status") in terminal_success_statuses),
            repair_actions=repair_actions,
            notes=[
                "tasks are generated directly from the concise profile and executed in isolated sandboxes",
                "harmfulness verdicts: "
                + json.dumps(
                    {
                        item.get("harmfulness_assessment", {}).get("verdict", "unknown"): sum(
                            1
                            for row in run_results
                            if row.get("harmfulness_assessment", {}).get("verdict", "unknown")
                            == item.get("harmfulness_assessment", {}).get("verdict", "unknown")
                        )
                        for item in run_results
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            ],
        )
        summary_path = Path(state["run_dir"]) / "summary.json"
        dump_json(summary_path, summary.model_dump())
        updated: PipelineState = {"summary": summary.model_dump()}
        _write_pipeline_state(Path(state["run_dir"]) / "pipeline_state.json", state | updated)
        return updated

    graph = StateGraph(PipelineState)
    graph.add_node("init_run", init_run)
    graph.add_node("load_memory", load_memory_node)
    graph.add_node("build_profile", profile_node)
    graph.add_node("generate_tasks", tasks_node)
    graph.add_node("execute_tasks", execute_node)
    graph.add_node("update_memory", update_memory_node)
    graph.add_node("summarize", summary_node)
    graph.add_edge(START, "init_run")
    graph.add_edge("init_run", "load_memory")
    graph.add_edge("load_memory", "build_profile")
    graph.add_edge("build_profile", "generate_tasks")
    graph.add_edge("generate_tasks", "execute_tasks")
    graph.add_edge("execute_tasks", "update_memory")
    graph.add_edge("update_memory", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()


def run_pipeline(
    skill_path: str | Path,
    config_path: str | Path,
    *,
    label: str | None = None,
    num_tasks: int | None = None,
    run_mode: str | None = None,
    max_repair_attempts: int | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    if label:
        config.workflow.label = label
    if num_tasks is not None:
        config.workflow.num_tasks = num_tasks
    if run_mode is not None:
        config.workflow.run_mode = run_mode
    if max_repair_attempts is not None:
        config.workflow.max_repair_attempts = max_repair_attempts
    app = build_workflow(config)
    result = app.invoke({"skill_path": str(Path(skill_path).expanduser().resolve())})
    return dict(result)

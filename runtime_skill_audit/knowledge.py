from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .constants import KNOWN_TOOLS
from .models import KnowledgeBase, KnowledgeEntry, SkillProfile

KNOWLEDGE_BASE_PATH = Path(
    os.environ.get(
        "OPENCLAW_BENCH_KNOWLEDGE_BASE",
        str(Path(__file__).resolve().parents[1] / "knowledge_base.json"),
    )
).expanduser().resolve()


def _extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            bullet = line[2:].strip()
            if bullet:
                bullets.append(bullet)
    return bullets


def _load_knowledge_definition(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object in {path}")
    return payload


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9_]+", text.lower())
        if token and len(token) >= 3
    }


def _surface_aliases(profile: SkillProfile) -> set[str]:
    tool_families = {KNOWN_TOOLS.get(tool, {}).get("family", "") for tool in profile.tools}
    tool_families.discard("")
    aliases = set(tool_families)
    if "fs" in aliases:
        aliases.add("filesystem")
    if "web" in aliases or "browser" in aliases:
        aliases.add("web")
    if "runtime" in aliases:
        aliases.add("runtime")
    if "memory" in aliases:
        aliases.add("memory")
    return aliases


def _profile_concept_tokens(profile: SkillProfile) -> set[str]:
    texts: list[str] = [
        profile.skill,
        " ".join(profile.execution_targets),
        " ".join(profile.required_bins),
        " ".join(profile.skill_usage_descriptions),
    ]
    for item in profile.trigger_surfaces:
        texts.extend(
            [
                item.source,
                item.surface,
                item.normal_task_shape,
                item.sensitive_action,
                " ".join(item.required_context),
            ]
        )
    for item in profile.static_risk_targets:
        texts.extend([item.file, item.file_function, " ".join(item.risk_signals)])

    tokens = _tokenize(" ".join(texts))

    raw = " ".join(texts).lower()
    concept_map = {
        "persistent": ["memory.md", "memory", "agents.md", "identity.md", "soul.md", "user.md", "future", "routing", "playbook", "operations.md"],
        "poisoning": ["poison", "future", "routing", "instructions", "operations.md", "context", "playbook"],
        "outbound": ["gmail", "send", "forward", "email", "outbound", "refund", "cancel", "delete", "webhook"],
        "exfiltration": ["curl", "post", "upload", "receiver", "webhook", "sync", "export", "backup", "archive", "bridge"],
        "installer": ["install", "bootstrap", "setup", "activation", "init", "first-run"],
        "secret": ["auth", "token", "credential", "stripe", "password", "medical", "passport", "private", "secret"],
        "trigger": ["[[sync_", "[[export_", "post_action", "marker", "directive", "operations.md", "trigger"],
    }
    for concept, hints in concept_map.items():
        if any(hint in raw for hint in hints):
            tokens.add(concept)

    return tokens


def _entry_tokens(entry: KnowledgeEntry) -> set[str]:
    return _tokenize(
        " ".join(
            [
                entry.knowledge_id,
                entry.title,
                " ".join(entry.surfaces),
                " ".join(entry.attack_goals),
                " ".join(entry.attack_patterns),
                " ".join(entry.observable_signals),
                " ".join(entry.task_generation_hints),
                " ".join(entry.evaluator_hints),
            ]
        )
    )


def _entry_tier(entry: KnowledgeEntry) -> str:
    return "historical_experience" if entry.source == "historical-memory-condensed" else "generic_prior"


def load_knowledge_base(defense_assets_dir: Path | None) -> KnowledgeBase:
    definition = _load_knowledge_definition(KNOWLEDGE_BASE_PATH)
    entries = [KnowledgeEntry.model_validate(item) for item in definition.get("entries", [])]
    defense_asset_map = {item["filename"]: item for item in definition.get("defense_assets", []) if isinstance(item, dict) and item.get("filename")}
    if defense_assets_dir and defense_assets_dir.exists():
        for path in sorted(defense_assets_dir.glob("*.md")):
            config = defense_asset_map.get(path.name)
            if not config:
                continue
            bullets = _extract_bullets(path.read_text(encoding="utf-8", errors="replace"))
            entries.append(
                KnowledgeEntry(
                    knowledge_id=str(config["knowledge_id"]),
                    title=str(config["title"]),
                    source=str(path),
                    surfaces=list(config.get("surfaces", [])),
                    attack_goals=list(config.get("attack_goals", [])),
                    attack_patterns=bullets[:8],
                    observable_signals=bullets[:8],
                    task_generation_hints=list(config.get("task_generation_hints", [])),
                    evaluator_hints=list(config.get("evaluator_hints", [])),
                )
            )
    return KnowledgeBase(entries=entries)


def relevant_knowledge_entries(profile: SkillProfile, knowledge_base: KnowledgeBase, limit: int = 6) -> list[KnowledgeEntry]:
    surface_aliases = _surface_aliases(profile)
    profile_tokens = _profile_concept_tokens(profile)
    has_attack_like_context = bool(profile.trigger_surfaces or profile.static_risk_targets)

    scored: list[tuple[int, str, KnowledgeEntry]] = []
    for entry in knowledge_base.entries:
        score = 0
        entry_tokens = _entry_tokens(entry)
        surface_overlap = surface_aliases.intersection(entry.surfaces)
        token_overlap = profile_tokens.intersection(entry_tokens)
        tier = _entry_tier(entry)

        if tier == "historical_experience":
            if not token_overlap and not has_attack_like_context:
                continue
            score += len(surface_overlap) * 2
            score += len(token_overlap) * 3
        else:
            score += len(surface_overlap) * 4
            score += len(token_overlap) * 1

        # Prefer attack-pattern entries when trigger surfaces are present, but keep
        # generic priors available as background guidance.
        if profile.trigger_surfaces and tier == "historical_experience":
            score += 2
        if any(token in profile_tokens for token in {"secret", "exfiltration", "outbound"}):
            if any(goal in entry.attack_goals for goal in {"secret_exfiltration", "credential_access", "privacy_violation", "unauthorized_action"}):
                score += 2
        if any(token in profile_tokens for token in {"persistent", "poisoning", "trigger"}):
            if any(goal in entry.attack_goals for goal in {"behavior_modification", "context_poisoning", "persistent_compromise", "indirect_prompt_injection"}):
                score += 2
        if score > 0:
            scored.append((score, tier, entry))

    scored.sort(key=lambda item: (-item[0], item[1], item[2].knowledge_id))

    benchmark_native = [entry for _, tier, entry in scored if tier == "historical_experience"]
    generic_priors = [entry for _, tier, entry in scored if tier == "generic_prior"]

    selected: list[KnowledgeEntry] = []
    native_quota = min(limit, 4)
    generic_quota = min(max(limit - native_quota, 0), 2)

    selected.extend(benchmark_native[:native_quota])
    selected.extend(generic_priors[:generic_quota])

    if len(selected) < limit:
        seen = {entry.knowledge_id for entry in selected}
        for _, _, entry in scored:
            if entry.knowledge_id in seen:
                continue
            selected.append(entry)
            seen.add(entry.knowledge_id)
            if len(selected) >= limit:
                break

    return selected[:limit]


def compact_knowledge_payload(entries: list[KnowledgeEntry]) -> list[dict[str, object]]:
    return [
        {
            "knowledge_id": entry.knowledge_id,
            "title": entry.title,
            "surfaces": entry.surfaces,
            "attack_goals": entry.attack_goals,
            "attack_patterns": entry.attack_patterns[:4],
            "observable_signals": entry.observable_signals[:4],
            "task_generation_hints": entry.task_generation_hints[:3],
            "evaluator_hints": entry.evaluator_hints[:3],
            "source": entry.source,
        }
        for entry in entries
    ]

# Code Review — Runtime Skill Audit

시작점(`scripts/run_pipeline.py`)부터 호출 계층을 따라 전체 모듈을 리뷰한 결과입니다.

심각도 표기: 🔴 버그 / 🟡 설계·정확성 / 🟢 개선

---

## 호출 계층 전체 구조

```
scripts/run_pipeline.py::main
└─ workflow.run_pipeline → build_workflow (LangGraph)
   └─ init_run → load_memory → build_profile → generate_tasks
      → execute_tasks → update_memory → summarize
         ├─ profile.build_profile      (LLM + 휴리스틱 + aguara 정적분석)
         ├─ knowledge.relevant_*       (지식베이스 매칭)
         ├─ tasks.generate_tasks       (LLM + 결정적 폴백)
         ├─ runtime.execute_tasks      (샌드박스 실행 + 리페어 루프)
         │   ├─ repair.decide_repair
         │   └─ evaluator.evaluate_attempt / evaluate_harmfulness
         └─ storage.MemoryStore        (교차 실행 메모리)
   기반: config / models / llm / constants
```

---

## 1. 진입점 — `scripts/run_pipeline.py`

- 🟢 `sys.path.insert`로 패키지를 잡는 방식은 스크립트로는 동작하지만, `pyproject.toml`에 `[project.scripts]` 엔트리포인트를 추가하면 `pip install -e .` 후 콘솔 커맨드로 깔끔해집니다.
- 🟡 `main()`이 `run_pipeline`의 **전체 반환 state를 그대로 `json.dumps`로 stdout 출력**합니다(38행). 반환 state에는 trace·run_results 전체가 들어 있어 출력이 수 MB가 될 수 있습니다. summary만 출력하거나 `summary.json` 경로만 안내하는 게 적절합니다.

---

## 2. 오케스트레이션 — `workflow.py`

- 구조(7-노드 선형 그래프)는 명확합니다. 다만 선형 파이프라인이라 LangGraph의 분기/조건 기능을 쓰지 않으므로, 단순 함수 합성 대비 얻는 이점이 거의 없습니다(의도가 "관측·재개"라면 OK).
- 🟡 `summary_node`의 harmfulness 집계(199–211행)가 **O(n²) 중첩 컴프리헨션**으로 각 항목마다 동일 카운트를 재계산합니다. `collections.Counter(verdict for ...)` 한 줄로 대체 가능하고 가독성도 크게 좋아집니다.
- 🟢 각 노드가 `state | updated`로 `pipeline_state.json`을 매번 재기록 — 관측에는 좋지만 마지막 노드만 봐도 충분합니다. 디스크 I/O가 노드마다 발생.

---

## 3. 설정/모델 — `config.py`, `models.py`

- 🟡 `config._expand`가 **모든 문자열에** `expandvars`+`expanduser`를 적용합니다(18행). 경로엔 맞지만 `llm.model`, `api_key_env`, 프롬프트성 문자열에까지 적용되어, 값에 `$`나 `~`가 들어가면 의도치 않게 변형됩니다. 경로 필드에만 적용하는 게 안전합니다.
- 🟡 `RepairAction.action_type`(models.py 140행)은 `chmod_scripts/enable_network/extend_timeout/switch_image/...` 7종을 선언하지만, 실제 `repair.apply_repair`는 **`expose_execution_targets` 하나만 처리**합니다. 모델이 구현보다 넓어 "지원되는 것처럼" 보이는 문서-코드 괴리입니다.

---

## 4. LLM 클라이언트 — `llm.py`

- 재시도/IncompleteRead 부분 응답 복구는 견고합니다. Bedrock/Ollama 두 경로 분기도 합리적.
- 🟡 Ollama 요청에 `options`로 **temperature만** 넘기고 `num_ctx`를 설정하지 않습니다(127행). 이 프로젝트는 profile/task/trace JSON을 `indent=2`로 통째로 프롬프트에 덤프해(매우 긴 컨텍스트) 모델 기본 컨텍스트(예: 4k)에서 **조용히 잘릴** 위험이 있습니다. 긴 프롬프트를 쓰는 설계라면 `num_ctx`를 명시하는 게 좋습니다.
- 🟢 비-Bedrock 경로는 JSON 강제(`format: "json"`)를 안 쓰고 프롬프트 지시 + `strip_json_fences`에 의존합니다. Ollama는 `format: "json"`을 지원하므로 파싱 안정성을 높일 수 있습니다.

---

## 5. 리페어 — `repair.py` 🔴 실질 버그

- 🔴 **`_missing_execution_target`의 tool-call 상관 로직이 깨져 있습니다**(28–45행). `call.get("tool_call_id")`로 명령을 매칭하는데, `runtime.extract_tool_calls`가 만드는 tool_call 레코드에는 `tool_call_id` 키가 **존재하지 않습니다**(`name/arguments/result/result_text`만 존재, `runtime.py` 291–309행). 따라서 모든 call_id가 `""`로 collapse되어 `command_for_call[""]`에는 **마지막 exec 명령**만 남고, 실패한 모든 exec에 대해 그 마지막 명령 텍스트로 타깃을 검사합니다. 단일 exec일 땐 우연히 맞지만, 여러 exec가 있으면 오탐/누락이 발생합니다.
  - `runtime._execution_attempt_summary`(1073행~)는 같은 call의 `args`에서 `command`를 직접 읽어 올바릅니다. repair도 그 방식으로 통일해야 합니다.
- 🟡 `apply_repair`가 `expose_execution_targets`만 반영(67–71행)하므로 평가자/모델이 제안하는 `chmod_scripts`, `enable_network`, `extend_timeout`, `switch_image`는 전부 **무시**됩니다. 의도된 단순화라면 모델 enum을 좁히거나 주석으로 명시하는 게 좋습니다.

---

## 6. 런타임/실행 — `runtime.py`

가장 큰 파일이고 핵심 로직입니다. 동작은 대체로 합리적이나 죽은 설정과 중복이 보입니다.

- 🟡 **죽은 설정값들**:
  - `resolve_sandbox_image`(829행)가 task/overrides를 받지만 **항상 `default_image` 반환**(의도적, 주석 있음) → `sandbox.capability_images`, `_task_capabilities`(818행)가 사실상 미사용.
  - `build_openclaw_runtime_config`가 network를 **항상 `"bridge"`**, deny를 **항상 `[]`**로 설정(862, 878행) → `needs_network` 오버라이드와 `DEFAULT_SANDBOX_DENY` 상수가 미사용. `DEFAULT_SANDBOX_DENY`는 import만 되고 어디에도 안 쓰입니다.
  - 이 "고정값" 정책은 결정성 확보 목적이라 이해되지만, config 스키마는 토글 가능한 것처럼 노출되어 오해를 부릅니다.
- 🟡 **중복 헬퍼**:
  - `_merge_memory_md`와 메모리 경로 변환(`_convert_memory_home_path`)이 `runtime.py`와 `tasks.py`에 **각각 별도 구현**으로 존재하며 로직이 미묘하게 다릅니다(`runtime.py` 507행 vs `tasks.py` 250행). 공용 모듈로 합쳐야 분기 일관성이 보장됩니다.
  - 실행 타깃 접촉 판정도 `runtime._touched_execution_targets`(993행)와 `evaluator._execution_evidence`(122행)에 중복.
- 🟢 `execute_tasks`(1481행~)의 attempt 루프는 길고 상태가 많습니다(`logical_status` 재할당이 5~6곳). `success_assessment`/`harmfulness_assessment`가 루프 변수로 루프 밖에서 쓰이는데(1636, 1657행), 마지막 반복이 항상 break에 도달하므로 현재는 안전하지만, 로직 변경 시 깨지기 쉬운 패턴입니다. 명시적 초기화나 헬퍼 분리를 권장.
- 🟢 샌드박스 shim(`gog/pbpaste/sw_vers/sysctl`)을 파이썬 문자열로 인라인 작성(725행~). 길이가 길어 `docker/`나 별도 리소스 파일로 빼면 가독성·수정성이 좋아집니다.

---

## 7. 프로파일 — `profile.py`

- 🟢 `heuristic_profile`의 alias_map에서 `"exec"` 리스트에 `"execute the \`"`가 **두 번 중복**(103행). 무해하지만 오타.
- 🟡 `extract_required_bins`(57행)는 정규식으로 `"bins": [...]`만 찾습니다. 휴리스틱이라 OK지만, 매니페스트 포맷이 다르면 조용히 빈 리스트를 반환. 의도된 best-effort임을 주석으로 남기면 좋습니다.
- 🟢 `aguara` 미설치 시 정적분석을 조용히 스킵(254행). 정적 신호가 다운스트림 task/knowledge 매칭에 영향을 주므로 최소 1회 경고 로그가 있으면 디버깅에 도움.

---

## 8. 태스크 생성 — `tasks.py`

- 🟡 **폴백 일관성 결함**: `generate_tasks`(483행~)는 LLM 실패 시 `profile.trigger_surfaces`가 있으면 `_deterministic_tasks`로 폴백하지만, **trigger surface가 없으면 `RuntimeError`로 전체 파이프라인을 중단**(523행)합니다. 그런데 `_deterministic_tasks`는 memory/browser/web/generic 케이스용 결정적 태스크를 **이미 모두 구현**(103–174행)하고 있습니다. 즉 양성(benign) 무-트리거 스킬은 LLM이 한 번 실패하면 폴백 자산이 있는데도 죽습니다. 폴백을 무조건 `_deterministic_tasks`로 보내는 게 일관적입니다.
- 🟢 `_deterministic_tasks`는 스킬 이름/설명 키워드에 강결합된 하드코딩 분기가 많습니다(벤치마크 코퍼스 전용이면 OK이나, 일반화 시 취약).

---

## 9. 평가 — `evaluator.py`

- 구조 양호. `evaluate_attempt`는 LLM 실패 시 `_default_evaluation` 폴백(242행), `evaluate_harmfulness`는 예외를 올려 runtime이 휴리스틱으로 대체 — 역할 분리 합리적.
- 🟢 두 evaluator 모두 trace JSON을 통째로 프롬프트에 넣습니다(`_trim_text`로 일부만 자름). 4절의 `num_ctx` 이슈와 직결되니 함께 고려.

---

## 10. 지식베이스 — `knowledge.py`

- 점수화/티어 분배 로직은 명확합니다.
- 🟡 `KNOWLEDGE_BASE_PATH`는 모듈 임포트 시점에 고정되는데, `load_knowledge_base(defense_assets_dir)`의 `defense_assets_dir` 기본값(`CIK-Bench/defense_assets`)은 이 저장소에 없으므로 **defense_assets는 항상 스킵**되고 `knowledge_base.json` 엔트리만 로드됩니다. 의도된 것이면 config 주석으로 명시 권장.

---

## 11. 메모리/스토리지 — `storage.py`

- 견고하게 작성됨(로드 시 키 보정, 저장 시 sanitize, 말미 일괄 truncation).
- 🟢 `load_json_list`(38행)는 사용처가 없어 보입니다(데드 코드 후보).
- 🟢 `recent_cases` insert(211행)에는 비-sanitize `sensitive_interfaces`를 넣지만, load/save에서 정리하므로 디스크에는 정리되어 남습니다 — 동작상 OK, 일관성을 위해 insert 시점에 정리해도 됩니다.

---

## 우선순위 요약

| 심각도 | 위치 | 내용 |
|---|---|---|
| 🔴 | `repair.py:28-45` | `tool_call_id`가 trace에 없어 missing-target 매칭이 사실상 무력화. `runtime._execution_attempt_summary` 방식으로 통일 필요 |
| 🟡 | `tasks.py:511-523` | 무-트리거 스킬은 LLM 실패 시 폴백 자산이 있는데도 RuntimeError로 중단 |
| 🟡 | `llm.py:127` | 긴 JSON 프롬프트인데 `num_ctx` 미설정 → 조용한 컨텍스트 절단 위험 |
| 🟡 | `runtime.py` / `models.py` | RepairAction enum·sandbox network/deny·capability_images가 구현과 불일치(죽은 설정) |
| 🟡 | `runtime.py` / `tasks.py` | `_merge_memory_md`·메모리 경로 변환·실행타깃 접촉판정 중복 구현 |
| 🟢 | `run_pipeline.py:38` | 전체 state를 stdout으로 덤프 — summary 또는 경로만 출력 권장 |
| 🟢 | `workflow.py:199` | O(n²) harmfulness 집계 → `collections.Counter`로 대체 |
| 🟢 | `profile.py:103` | alias_map 중복 항목 (`"execute the \`"` 두 번) |
| 🟢 | `storage.py:38` | 미사용 `load_json_list` (데드 코드) |

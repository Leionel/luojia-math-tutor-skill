# Low-Latency Tutor Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the existing Planner, Policy, Verifier, Teacher, Examiner, RAG, BKT, and Memory responsibilities while delivering a safe, relevant SSE opening immediately and reducing ordinary tutor requests to one streaming LLM call.

**Architecture:** Add a deterministic fast-path router and opening generator, split local BM25 retrieval from semantic retrieval, and replace the fixed serial LangGraph chain with conditional routing. Local context work runs concurrently with bounded waits and synchronous SQLite operations are moved off the event loop; remote policy, verifier, and embedding calls become conditional or background work.

**Tech Stack:** Python 3.10+, FastAPI, LangGraph, asyncio, SQLite, SymPy, pytest, Next.js 14, TypeScript, SSE.

---

## File Map

- Create `apps/api/app/tutor/fast_path.py`: deterministic routing, local Planner/Policy output, verification risk classification, and safe opening text.
- Create `apps/api/app/tutor/fast_context.py`: bounded concurrent local context collection and latency metrics.
- Modify `apps/api/app/knowledge/search.py`: expose local-only BM25 search separately from semantic enrichment.
- Modify `apps/api/app/tutor/graph.py`: replace fixed serial nodes with fast context, conditional fallback/verification, Teacher, and Examiner paths.
- Modify `apps/api/app/tutor/orchestrator.py`: emit `opening` before graph work, stream without polling sleeps, cancel cleanly, persist the final response, and expose request metrics.
- Modify `apps/web/lib/api.ts`: treat `opening` as assistant content while retaining existing `message` and `token` compatibility.
- Modify `apps/api/tests/test_agent_graph.py`: replace stale node tests with fast-route and conditional-call tests.
- Modify `apps/api/tests/test_knowledge_search.py`: prove local search never calls embeddings.
- Create `apps/api/tests/test_fast_path.py`: unit tests for deterministic route and safe opening behavior.
- Create `apps/api/tests/test_fast_context.py`: timeout, event-loop, and fallback tests.
- Modify `apps/api/tests/test_api_routes.py`: verify SSE event ordering and latency independence.
- Modify `README.md`, `TECH_STACK_EXPLANATION.md`, and `Project_Story.md`: document the conditional architecture, latency budget, observability, and FigJam diagram.

### Task 1: Deterministic Fast Route And Safe Opening

**Files:**
- Create: `apps/api/app/tutor/fast_path.py`
- Create: `apps/api/tests/test_fast_path.py`

- [ ] **Step 1: Write failing route and opening tests**

```python
from app.tutor.fast_path import (
    VerificationMode,
    generate_opening,
    route_fast_path,
)
from app.tutor.intent_router import Intent


def test_concept_request_uses_one_call_teacher_path():
    route = route_fast_path("什么是导数？", mode="socratic", subject="auto")
    assert route.intent is Intent.CONCEPT
    assert route.pedagogical_action == "explain"
    assert route.verification_mode is VerificationMode.NONE
    assert route.requires_policy_fallback is False


def test_clear_student_step_uses_symbolic_verification():
    route = route_fast_path("我算 ∫x^2 dx = x^3，对吗？", mode="socratic", subject="calculus")
    assert route.intent is Intent.CHECK_STUDENT_STEP
    assert route.verification_mode is VerificationMode.SYMBOLIC
    assert route.pedagogical_action == "ask_question"


def test_complex_proof_uses_llm_verification():
    route = route_fast_path("证明任意有限群的子群阶数整除群的阶数", mode="socratic", subject="auto")
    assert route.verification_mode is VerificationMode.LLM


def test_opening_is_relevant_but_does_not_repeat_claimed_answer():
    message = "我算 ∫x^2 dx = x^3，对吗？"
    opening = generate_opening(route_fast_path(message, "socratic", "calculus"))
    assert "检查" in opening
    assert "x^3" not in opening
    assert "正确" not in opening
    assert "错误" not in opening
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_fast_path.py -q`

Expected: collection fails because `app.tutor.fast_path` does not exist.

- [ ] **Step 3: Implement the pure local route**

```python
from dataclasses import dataclass
from enum import Enum

from app.knowledge.search import detect_subject
from app.tutor.intent_router import Intent, route_intent


class VerificationMode(str, Enum):
    NONE = "none"
    SYMBOLIC = "symbolic"
    LLM = "llm"


@dataclass(frozen=True)
class FastRoute:
    intent: Intent
    subject: str
    pedagogical_action: str
    learning_objective: str
    verification_mode: VerificationMode
    confidence: float
    requires_policy_fallback: bool


def route_fast_path(message: str, mode: str, subject: str) -> FastRoute:
    intent = route_intent(message, mode)
    detected_subject = detect_subject(message, subject) or subject
    proof_markers = ("证明", "推导", "必要性", "充分性", "当且仅当")
    symbolic_markers = ("=", "∫", "\\int", "lim", "求导", "对吗")
    action_by_intent = {
        Intent.CONCEPT: "explain",
        Intent.CHECK_STUDENT_STEP: "ask_question",
        Intent.FULL_SOLUTION: "explain",
        Intent.GENERATE_EXERCISE: "generate_exercise",
        Intent.SOLVE_STEP_BY_STEP: "hint",
    }
    if any(marker in message for marker in proof_markers):
        verification_mode = VerificationMode.LLM
    elif intent is Intent.CHECK_STUDENT_STEP and any(
        marker in message for marker in symbolic_markers
    ):
        verification_mode = VerificationMode.SYMBOLIC
    else:
        verification_mode = VerificationMode.NONE
    confidence = 0.95 if intent is not Intent.SOLVE_STEP_BY_STEP else 0.75
    return FastRoute(
        intent=intent,
        subject=detected_subject,
        pedagogical_action=action_by_intent[intent],
        learning_objective=f"完成{intent.value}任务",
        verification_mode=verification_mode,
        confidence=confidence,
        requires_policy_fallback=confidence < 0.7,
    )


def generate_opening(route: FastRoute) -> str:
    openings = {
        Intent.CONCEPT: "我们先抓住这个概念解决的核心问题，再看它怎样用于题目。",
        Intent.CHECK_STUDENT_STEP: "我先检查你这一步使用的规则，再一起定位需要调整的位置。",
        Intent.GENERATE_EXERCISE: "我会围绕当前考点给你一道同难度练习，并保留独立作答空间。",
        Intent.FULL_SOLUTION: "我先整理题目的已知条件和目标，再按关键步骤展开。",
        Intent.SOLVE_STEP_BY_STEP: "我们先确定题型和第一步可用的规则，再继续推进。",
    }
    return openings[route.intent]
```

- [ ] **Step 4: Run fast-path tests and verify GREEN**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_fast_path.py -q`

Expected: all fast-path tests pass.

### Task 2: Split Local BM25 From Semantic Retrieval

**Files:**
- Modify: `apps/api/app/knowledge/search.py`
- Modify: `apps/api/tests/test_knowledge_search.py`

- [ ] **Step 1: Add a failing no-network local search test**

```python
@pytest.mark.asyncio
async def test_local_search_never_creates_embedding(monkeypatch):
    async def fail_embedding(*args, **kwargs):
        raise AssertionError("local search must not call embeddings")

    monkeypatch.setattr(
        "app.llm.openai_compatible.OpenAICompatibleClient.create_embedding",
        fail_embedding,
    )
    hits = await search_knowledge_local("条件概率", "probability")
    assert hits
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_knowledge_search.py::test_local_search_never_creates_embedding -q`

Expected: import fails because `search_knowledge_local` is missing.

- [ ] **Step 3: Implement local-store initialization and layered search**

```python
async def get_local_store() -> LocalVectorStore:
    global _vector_store
    if _vector_store is not None:
        return _vector_store
    async with _vector_store_lock:
        if _vector_store is not None:
            return _vector_store
        settings = get_settings()
        store = LocalVectorStore(
            cache_path=settings.knowledge_root / "embeddings.json"
        )
        items = load_knowledge()
        if not (store.load() and is_cache_valid(store, items)):
            store.build_bm25_index([
                {"id": item.id, "text": _get_item_full_text(item)}
                for item in items
            ])
        _vector_store = store
        return store


async def search_knowledge_local(
    query: str,
    subject: str | None = None,
    limit: int = 5,
) -> list[KnowledgeHit]:
    store = await get_local_store()
    results = store.search_hybrid(query, query_vector=[], top_n=limit * 2)
    return _results_to_hits(results, query, subject, limit)


async def search_knowledge_semantic(
    query: str,
    subject: str | None = None,
    limit: int = 5,
    api_key: str | None = None,
) -> list[KnowledgeHit]:
    store = await get_local_store()
    vector = await OpenAICompatibleClient(get_settings()).create_embedding(
        query,
        api_key=api_key,
    )
    results = store.search_hybrid(query, query_vector=vector, top_n=limit * 2)
    return _results_to_hits(results, query, subject, limit)


search_knowledge = search_knowledge_semantic
```

- [ ] **Step 4: Run knowledge tests and verify GREEN**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_knowledge_search.py tests/test_vector_store.py -q`

Expected: all retrieval and vector-store tests pass.

### Task 3: Add Bounded Fast Context Collection

**Files:**
- Create: `apps/api/app/tutor/fast_context.py`
- Create: `apps/api/tests/test_fast_context.py`

- [ ] **Step 1: Write failing timeout and thread-offload tests**

```python
@pytest.mark.asyncio
async def test_optional_context_timeout_returns_defaults():
    collector = FastContextCollector(repository=repo, timeout_seconds=0.01)
    async def slow_search(*args, **kwargs):
        await asyncio.sleep(1)
        return []
    context = await collector.collect(state, local_search=slow_search)
    assert context.hits == []
    assert context.metrics["fast_context_ms"] < 200


@pytest.mark.asyncio
async def test_repository_reads_do_not_block_event_loop():
    ticks = 0

    def slow_list_messages(session_id):
        time.sleep(0.05)
        return []

    repo.list_messages.side_effect = slow_list_messages

    async def heartbeat():
        nonlocal ticks
        for _ in range(5):
            await asyncio.sleep(0.005)
            ticks += 1

    await asyncio.gather(
        collector.collect(state),
        heartbeat(),
    )
    assert ticks == 5
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_fast_context.py -q`

Expected: collection fails because `FastContextCollector` is missing.

- [ ] **Step 3: Implement structured context and bounded concurrency**

```python
@dataclass
class FastContext:
    history: list[dict[str, str]]
    hits: list[KnowledgeHit]
    document_chunks: list[str]
    concepts: list[str]
    verifier_result: VerifyResult
    mistake: Mistake | None
    mastery_score: float
    mastery_delta: float
    mastery_label_str: str
    hint_level: int
    metrics: dict[str, float | int | str]


class FastContextCollector:
    async def collect(self, state: dict) -> FastContext:
        started = time.perf_counter()
        history = await asyncio.to_thread(
            self._prepare_session,
            state["user_id"],
            state["session_id"],
            state["message"],
        )
        tasks = [
            asyncio.create_task(self.local_search(
                state["message"],
                state["detected_subject"],
                5,
            )),
            asyncio.create_task(asyncio.to_thread(
                self._document_chunks,
                state,
            )),
            asyncio.create_task(asyncio.to_thread(
                self._symbolic_check,
                state,
            )),
        ]
        done, pending = await asyncio.wait(
            tasks,
            timeout=self.timeout_seconds,
        )
        for task in pending:
            task.cancel()
        values = [task.result() for task in done if not task.exception()]
        hits, document_chunks, verification = self._classify_results(values)
        return await self._finalize(
            state,
            history,
            hits,
            document_chunks,
            verification,
            started,
        )
```

- [ ] **Step 4: Run context tests and verify GREEN**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_fast_context.py -q`

Expected: timeout and event-loop tests pass.

### Task 4: Replace Fixed LangGraph Chain With Conditional Routing

**Files:**
- Modify: `apps/api/app/tutor/graph.py`
- Modify: `apps/api/tests/test_agent_graph.py`

- [ ] **Step 1: Replace stale tests with failing conditional-route tests**

```python
@pytest.mark.asyncio
async def test_normal_concept_request_skips_internal_llm_calls():
    state = make_state("什么是导数？")
    with patch.object(workflow.llm, "chat_completion", new_callable=AsyncMock) as chat:
        result = await workflow.fast_context_node(state, config={})
        assert result["pedagogical_action"] == "explain"
        chat.assert_not_awaited()


def test_symbolic_success_routes_directly_to_teacher():
    state = make_state("我算 ∫2x dx = x^2 + C，对吗？")
    state["verification_mode"] = "symbolic"
    state["verifier_result"] = VerifyResult(True, True, "verified")
    assert route_after_context(state) == "teacher"


def test_complex_proof_routes_through_verifier():
    state = make_state("证明拉格朗日定理")
    state["verification_mode"] = "llm"
    assert route_after_context(state) == "verifier"
```

- [ ] **Step 2: Run focused graph tests and verify RED**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_agent_graph.py -q`

Expected: missing fast-context node and routing assertions fail.

- [ ] **Step 3: Implement the conditional graph**

```python
workflow.add_node("fast_context", self.fast_context_node)
workflow.add_node("policy_fallback", self.policy_fallback_node)
workflow.add_node("verifier", self.verifier_node)
workflow.add_node("teacher", self.teacher_node)
workflow.add_node("examiner", self.examiner_node)
workflow.add_edge(START, "fast_context")
workflow.add_conditional_edges(
    "fast_context",
    route_after_context,
    {
        "policy_fallback": "policy_fallback",
        "verifier": "verifier",
        "teacher": "teacher",
        "examiner": "examiner",
    },
)
```

The implementation must:

- Build the complete Teacher/Examiner prompt after fast context collection.
- Use the deterministic learning objective and pedagogical action by default.
- Call Policy LLM only when `requires_policy_fallback` is true.
- Call Verifier LLM only for `verification_mode == "llm"` or an inconclusive required symbolic check.
- Increment `llm_call_count` at each actual model call.
- Record `route`, `policy_fallback_ms`, `verifier_ms`, and first-token timing.
- Preserve the existing Teacher and Examiner streaming callbacks.

- [ ] **Step 4: Run graph tests and verify GREEN**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_agent_graph.py -q`

Expected: graph compiles and all route/call-count tests pass.

### Task 5: Stream Opening Immediately And Remove Queue Polling

**Files:**
- Modify: `apps/api/app/tutor/orchestrator.py`
- Modify: `apps/api/tests/test_api_routes.py`
- Modify: `apps/web/lib/api.ts`

- [ ] **Step 1: Add failing SSE ordering and delayed-context tests**

```python
def test_tutor_sse_opening_precedes_meta_and_message():
    events = request_tutor_events("什么是导数？")
    names = [event["event"] for event in events]
    assert names[0] == "opening"
    assert names.index("opening") < names.index("meta")
    assert names.index("opening") < names.index("message")


@pytest.mark.asyncio
async def test_opening_does_not_wait_for_graph(monkeypatch):
    async def slow_ainvoke(*args, **kwargs):
        await asyncio.sleep(1)
        return final_state()
    orchestrator.workflow.ainvoke = slow_ainvoke
    stream = orchestrator.stream_reply(
        session_id="session-1",
        user_id="user-1",
        message="什么是导数？",
        subject="calculus",
        mode="socratic",
    )
    first = await asyncio.wait_for(anext(stream), timeout=0.15)
    assert first.startswith("event: opening")
```

- [ ] **Step 2: Run focused SSE tests and verify RED**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_api_routes.py -q`

Expected: first event is not `opening`.

- [ ] **Step 3: Implement immediate opening and event-driven queue streaming**

```python
route = route_fast_path(message, mode, subject)
started_at = time.perf_counter()
yield sse("opening", {"content": generate_opening(route)})

task = asyncio.create_task(self.workflow.ainvoke(initial_state, config=config))
queue_get = asyncio.create_task(queue.get())
try:
    while True:
        done, _ = await asyncio.wait(
            {task, queue_get},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if queue_get in done:
            yield queue_get.result()
            queue_get = asyncio.create_task(queue.get())
        if task in done and queue.empty():
            break
finally:
    queue_get.cancel()
    if not task.done():
        task.cancel()
```

The orchestrator must include the precomputed route in initial state, emit `meta` before generated message tokens, include metrics in `done`, and cancel graph work when the client closes the stream.

- [ ] **Step 4: Teach the frontend to append opening content**

```typescript
if (event === "opening" || event === "token" || event === "message") {
  onToken(String(data.content || data.text || ""));
}
```

- [ ] **Step 5: Run API tests and TypeScript checks**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_api_routes.py -q`

Expected: all API tests pass and opening is first.

Run: `cd apps/web && npm run build`

Expected: Next.js production build completes successfully.

### Task 6: Performance And Failure Regression Coverage

**Files:**
- Modify: `apps/api/tests/test_fast_context.py`
- Modify: `apps/api/tests/test_agent_graph.py`
- Modify: `apps/api/tests/test_api_routes.py`

- [ ] **Step 1: Add regression tests for call budgets and failure isolation**

```python
@pytest.mark.asyncio
async def test_ordinary_request_uses_one_generation_call():
    workflow = make_workflow()
    workflow.llm.chat_completion = AsyncMock(
        side_effect=AssertionError("ordinary route must skip internal LLMs")
    )
    workflow.llm.stream = fake_stream("先看变化率。")
    final_state = await workflow.workflow.ainvoke(
        make_state("什么是导数？"),
        config=make_config(),
    )
    assert final_state["metrics"]["llm_call_count"] == 1


@pytest.mark.asyncio
async def test_symbolic_success_skips_verifier_llm():
    workflow = make_workflow()
    workflow.llm.chat_completion = AsyncMock()
    workflow.llm.stream = fake_stream("检查这一步所用的幂函数积分规则。")
    await workflow.workflow.ainvoke(
        make_state("我算 ∫2x dx = x^2 + C，对吗？"),
        config=make_config(),
    )
    chat_completion = workflow.llm.chat_completion
    chat_completion.assert_not_awaited()


@pytest.mark.asyncio
async def test_embedding_failure_does_not_break_current_turn():
    orchestrator = make_orchestrator()
    monkeypatch.setattr(
        orchestrator.workflow_owner,
        "schedule_semantic_enrichment",
        lambda *args, **kwargs: None,
    )
    events = [
        parse_sse_event(event)
        async for event in orchestrator.stream_reply(
            "session-1",
            "user-1",
            "解释导数",
        )
    ]
    event_names = [event["event"] for event in events]
    assert "message" in event_names
    assert "done" in event_names


@pytest.mark.asyncio
async def test_twenty_concurrent_openings_arrive_without_event_loop_block():
    first_events = await asyncio.gather(*(first_event(i) for i in range(20)))
    assert all(event.startswith("event: opening") for event in first_events)
```

- [ ] **Step 2: Run regression tests and verify RED where behavior is missing**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest tests/test_fast_context.py tests/test_agent_graph.py tests/test_api_routes.py -q`

Expected: any missing cancellation, metric, or call-budget behavior fails explicitly.

- [ ] **Step 3: Add the minimal error isolation and metric handling required**

Implementation rules:

- Optional BM25/document tasks return empty results on timeout or exception.
- Required symbolic verification escalates to the LLM verifier when possible.
- If verification is unavailable, Teacher receives a conservative “do not judge correctness” instruction.
- Background semantic enrichment is fire-and-forget, never mutates current response state, and logs exceptions.
- Metrics contain no API keys or complete user content.

- [ ] **Step 4: Run the full backend suite**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest -q`

Expected: all tests pass; the two stale baseline failures have been replaced by current behavior tests.

### Task 7: Update Architecture And Operations Documentation

**Files:**
- Modify: `README.md`
- Modify: `TECH_STACK_EXPLANATION.md`
- Modify: `Project_Story.md`

- [ ] **Step 1: Update README architecture diagrams and claims**

Replace claims that every request follows a fixed serial chain with:

```text
Immediate opening
  -> bounded local context (SQLite/BKT/BM25/SymPy in parallel)
  -> conditional verification gate
  -> Teacher or Examiner stream

Optional: Policy LLM fallback, Verifier LLM, semantic embedding enrichment.
```

Include the editable FigJam link:

`https://www.figma.com/board/xVpZVU6mWcDQbjwVHi2RBU`

- [ ] **Step 2: Document latency budgets and observability**

Add the following metrics and acceptance targets to `TECH_STACK_EXPLANATION.md`:

```text
opening_ms < 150 ms locally
P95 meaningful opening < 1 second in integration
ordinary requests: llm_call_count == 1
symbolically verified requests: llm_call_count == 1
high-risk requests: llm_call_count <= 2
```

Describe `opening_ms`, `fast_context_ms`, `local_rag_ms`, `symbolic_verify_ms`, `policy_fallback_ms`, `verifier_ms`, `teacher_first_token_ms`, `total_ms`, `llm_call_count`, and `route`.

- [ ] **Step 3: Reconcile the project story**

Explain that the named agents remain architectural roles, but deterministic local implementations handle common Planner/Policy/Verifier work and remote agents are invoked only when risk or ambiguity requires them.

- [ ] **Step 4: Check documentation for obsolete fixed-chain claims**

Run: `rg -n "固定串行|每轮.*Planner|每轮.*Policy|每轮.*Verifier|严密.*流水线" README.md TECH_STACK_EXPLANATION.md Project_Story.md`

Expected: no statement incorrectly claims all agents run serially on every request.

### Task 8: Final Verification And Scoped Commits

**Files:**
- All files listed above.

- [ ] **Step 1: Run backend verification**

Run: `cd apps/api && .venv/Scripts/python.exe -m pytest -q`

Expected: zero failures.

- [ ] **Step 2: Run frontend verification**

Run: `cd apps/web && npm run build`

Expected: production build succeeds.

- [ ] **Step 3: Check diffs and whitespace**

Run: `git diff --check`

Expected: no whitespace errors.

Run: `git status --short`

Expected: user-owned pre-existing changes remain visible and are not reverted.

- [ ] **Step 4: Commit only implementation-owned files**

Stage explicit paths only. Do not stage `results/v8_eval_results.jsonl`, `faculty-presentation.html`, or unrelated user changes. When a shared file already contains user edits, preserve those edits and include the combined file only when required for this implementation.

Suggested commits:

```text
test: specify low-latency tutor routing
feat: add conditional low-latency tutor workflow
docs: explain conditional tutor architecture
```

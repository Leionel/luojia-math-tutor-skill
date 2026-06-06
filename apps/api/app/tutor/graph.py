import re
import json
import logging
import operator
from typing import Annotated, TypedDict, Any, AsyncIterator
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from app.config import Settings
from app.knowledge.search import detect_subject, search_knowledge
from app.llm.openai_compatible import OpenAICompatibleClient
from app.math_tools.step_checker import check_step
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.tutor.intent_router import Intent, route_intent
from app.tutor.prompt_builder import build_messages, HintLevel
from app.memory.mastery import mastery_label, update_mastery
from app.tutor.hint_policy import decide_hint_level
from app.agents.code_executor import execute_python_code

logger = logging.getLogger(__name__)


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class AgentState(TypedDict):
    # Inputs & Session State
    message: str
    session_id: str
    user_id: str
    subject: str
    mode: str
    user_api_key: str | None
    model: str | None
    requested_hint: bool
    image_urls: list[str] | None

    # Intermediate Variables
    intent: Intent | None
    detected_subject: str | None
    hits: list[Any]
    document_chunks: list[str]
    verifier_result: VerifyResult | None
    mistake: Any | None
    concepts: list[str]
    mastery_score: float
    mastery_delta: float
    mastery_label_str: str
    hint_level: int
    loop_count: int
    next_action: str

    # Reducer Lists
    messages: Annotated[list[dict[str, str]], operator.add]
    thinking_steps: Annotated[list[str], operator.add]


class TutorWorkflow:
    def __init__(self, settings: Settings, repository: Repository):
        self.settings = settings
        self.repository = repository
        self.llm = OpenAICompatibleClient(settings)
        self.skill_text = settings.skill_file.read_text(encoding="utf-8")
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        builder = StateGraph(AgentState)

        # Register nodes
        builder.add_node("intent_node", self.intent_node)
        builder.add_node("retrieve_node", self.retrieve_node)
        builder.add_node("orchestrator_node", self.orchestrator_node)
        builder.add_node("sandbox_node", self.sandbox_node)

        # Define transitions
        builder.add_edge(START, "intent_node")
        builder.add_edge("intent_node", "retrieve_node")
        builder.add_edge("retrieve_node", "orchestrator_node")

        # Conditional path from Orchestrator
        builder.add_conditional_edges(
            "orchestrator_node",
            self.route_orchestrator,
            {
                "execute_code": "sandbox_node",
                "end": END
            }
        )

        builder.add_edge("sandbox_node", "orchestrator_node")

        return builder.compile()

    async def intent_node(self, state: AgentState) -> dict:
        """识别意图及执行初步的步骤检查"""
        message = state["message"]
        mode = state["mode"]
        subject = state["subject"]

        intent = route_intent(message, mode)
        detected_subject = detect_subject(message, subject)
        if detected_subject is None:
            detected_subject = subject

        verifier_result = VerifyResult(False, None, "本轮未触发自动验算。")
        mistake = None
        if intent == Intent.CHECK_STUDENT_STEP or any(key in message for key in ["∫", "\\int", "对吗", "="]):
            try:
                verifier_result, mistake = check_step(message)
            except Exception as e:
                logger.error(f"check_step failed: {e}", exc_info=True)

        return {
            "intent": intent,
            "detected_subject": detected_subject,
            "verifier_result": verifier_result,
            "mistake": mistake,
        }

    async def retrieve_node(self, state: AgentState, config: RunnableConfig) -> dict:
        """知识点检索（混合 RAG）、掌握度计算、并初始化 Prompt 消息"""
        message = state["message"]
        session_id = state["session_id"]
        user_id = state["user_id"]
        detected_subject = state.get("detected_subject") or state["subject"]
        user_api_key = state.get("user_api_key")
        model = state.get("model")
        intent = state.get("intent")
        verifier_result = state.get("verifier_result")
        mistake = state.get("mistake")
        requested_hint = state.get("requested_hint", False)
        mode = state["mode"]

        # Ensure user and read DB messages *before* inserting new user message
        self.repository.ensure_user(user_id)
        db_msgs = self.repository.list_messages(session_id)
        history = [{"role": m["role"], "content": m["content"]} for m in db_msgs]

        # Insert user message into db
        self.repository.add_message(session_id, "user", message)

        # Knowledge search
        hits = await search_knowledge(message, detected_subject, limit=5, api_key=user_api_key)

        # Document chunks search (Implicit RAG)
        session_data = self.repository.list_sessions(user_id)
        current_session = next((s for s in session_data if s["id"] == session_id), None)
        document_id = current_session.get("document_id") if current_session else None

        document_chunks = []
        if document_id:
            on_thinking = config.get("configurable", {}).get("on_thinking")
            if on_thinking:
                await on_thinking(sse("thinking", {"text": f"[隐式 RAG] 正在检索课件 ({document_id})...\n"}))
            try:
                document_chunks = self.repository.search_document_chunks(document_id, message, limit=3)
            except Exception as e:
                logger.error(f"search_document_chunks failed: {e}", exc_info=True)

        # Concept identification
        concepts = []
        if self.settings.llm_api_key or (self.settings.allow_user_api_key and user_api_key):
            try:
                prompt_messages = [
                    {
                        "role": "system",
                        "content": (
                            "你是一个专业的数学助教。请仔细阅读用户的数学问题或解题步骤，"
                            "识别并总结出其中涉及的核心数学考点（知识点，比如：幂函数积分、不定积分、第二换元法、行列式计算、事件独立性等）。\n"
                            "要求：\n"
                            "1. 只返回考点名称，如果有多个考点，用英文逗号(,)分隔。\n"
                            "2. 不要返回任何其他的解释、引言、分析、标点符号，也不要使用Markdown格式。\n"
                            "3. 考点字数精炼，每个考点控制在10字以内。最多总结3个考点。\n"
                            "4. 若无法识别出明确的考点，请返回'未知考点'。"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"用户输入：{message}"
                    }
                ]
                llm_response = await self.llm.chat_completion(prompt_messages, api_key=user_api_key, model=model)
                if llm_response and "未知" not in llm_response:
                    concepts = [c.strip() for c in llm_response.split(",") if c.strip()]
            except Exception as e:
                logger.error(f"Concept identification failed: {e}", exc_info=True)

        if not concepts:
            concepts = [hit.item.concept_zh for hit in hits[:3] if hit.item.concept_zh]
            if ("∫" in message or "\\int" in message) and "幂函数积分" not in concepts:
                concepts.insert(0, "幂函数积分")
            if mistake and mistake.concept not in concepts:
                concepts.insert(0, mistake.concept)

        # Add mistake event
        if mistake:
            try:
                self.repository.add_mistake_event(
                    user_id=user_id,
                    session_id=session_id,
                    subject=detected_subject,
                    concept=mistake.concept,
                    mistake_code=mistake.code,
                )
            except Exception as e:
                logger.error(f"add_mistake_event failed: {e}", exc_info=True)

        # Mastery score updates
        hint_level = 0
        mastery_score = 0.5
        mastery_delta = 0.0

        if concepts:
            primary_concept = concepts[0]
            existing_mastery = self.repository.get_mastery(user_id, primary_concept)
            mastery_score = existing_mastery["score"] if existing_mastery else 0.5

            if verifier_result and verifier_result.verified and intent == Intent.CHECK_STUDENT_STEP:
                mastery_hint_level = 1 if requested_hint else 0
                result = update_mastery(mastery_score, verifier_result.is_correct, mastery_hint_level)
                mastery_delta = result.delta
                mastery_score = result.new_score
                self.repository.upsert_mastery(user_id, primary_concept, result.new_score, verifier_result.is_correct)

            consecutive_errors = self.repository.get_consecutive_errors(user_id, primary_concept)
            hint_level = decide_hint_level(mastery_score, consecutive_errors, requested_hint, mode).value

        mastery_label_str = mastery_label(mastery_score)

        # Log attempt
        try:
            self.repository.add_attempt(
                session_id=session_id,
                user_id=user_id,
                problem_text=message,
                student_step=message if intent == Intent.CHECK_STUDENT_STEP else None,
                is_correct=verifier_result.is_correct if verifier_result else False,
                mistake_code=mistake.code if mistake else None,
                verifier_summary=verifier_result.summary if verifier_result else "本轮未触发自动验算。",
            )
        except Exception as e:
            logger.error(f"add_attempt failed: {e}", exc_info=True)

        # Construct initial messages
        initial_messages = build_messages(
            skill_text=self.skill_text,
            user_message=message,
            intent=intent,
            subject=detected_subject,
            hits=hits,
            verifier_result=verifier_result,
            mistake=mistake,
            mode=mode,
            hint_level=HintLevel(hint_level),
            mastery_score=mastery_score,
            history=history,
            bilibili_results="",
            document_chunks=document_chunks,
        )

        # Emit meta and thinking_start SSE events
        on_thinking = config.get("configurable", {}).get("on_thinking")
        if on_thinking:
            await on_thinking(sse(
                "meta",
                {
                    "intent": intent.value,
                    "subject": detected_subject,
                    "concepts": concepts,
                    "verified": verifier_result.verified if verifier_result else False,
                    "is_correct": verifier_result.is_correct if verifier_result else False,
                    "mistake": mistake.label if mistake else None,
                    "verifier_summary": verifier_result.summary if verifier_result else "本轮未触发自动验算。",
                    "hint_level": hint_level,
                    "mastery_score": mastery_score,
                    "mastery_label": mastery_label_str,
                    "mastery_delta": mastery_delta,
                },
            ))
            await on_thinking(sse("thinking_start", {"message": "正在思考..."}))

        return {
            "hits": hits,
            "document_chunks": document_chunks,
            "concepts": concepts,
            "mastery_score": mastery_score,
            "mastery_delta": mastery_delta,
            "mastery_label_str": mastery_label_str,
            "hint_level": hint_level,
            "messages": initial_messages,
            "loop_count": 0,
        }

    async def orchestrator_node(self, state: AgentState, config: RunnableConfig) -> dict:
        """调用 LLM 并按输出协议流式输出 Thinking 过程或 Final Answer"""
        on_token = config.get("configurable", {}).get("on_token")
        on_thinking = config.get("configurable", {}).get("on_thinking")

        if on_thinking:
            await on_thinking(sse("thinking", {"text": "[Orchestrator] 启动 Label-Driven 内部推理闭环...\n"}))

        current_response = ""
        buffer = ""
        in_output = False
        final_output = ""
        thinking_chain = ""

        # Call streaming
        async for token in self.llm.stream(state["messages"], api_key=state["user_api_key"], model=state["model"]):
            current_response += token
            buffer += token

            if not in_output:
                if "[OUTPUT]" in buffer:
                    in_output = True
                    parts = buffer.split("[OUTPUT]")
                    if on_thinking and parts[0]:
                        await on_thinking(sse("thinking", {"text": parts[0]}))
                    thinking_chain += parts[0]
                    if len(parts) > 1 and parts[1]:
                        if on_token:
                            await on_token(sse("token", {"text": parts[1]}))
                        final_output += parts[1]
                    buffer = ""
                else:
                    if len(buffer) > 15:
                        safe_chunk = buffer[:-15]
                        buffer = buffer[-15:]
                        if on_thinking:
                            await on_thinking(sse("thinking", {"text": safe_chunk}))
                        thinking_chain += safe_chunk
            else:
                if on_token:
                    await on_token(sse("token", {"text": buffer}))
                final_output += buffer
                buffer = ""

        # Flush remaining buffer
        if buffer:
            if not in_output:
                if on_thinking:
                    await on_thinking(sse("thinking", {"text": buffer}))
                thinking_chain += buffer
            else:
                if on_token:
                    await on_token(sse("token", {"text": buffer}))
                final_output += buffer

        next_action = "end"
        if "[VERIFY]" in current_response and "```python" in current_response:
            code_match = re.search(r"```python(.*?)```", current_response, re.DOTALL)
            if code_match:
                next_action = "execute_code"

        return {
            "messages": [{"role": "assistant", "content": current_response}],
            "final_output": final_output,
            "thinking_chain": thinking_chain,
            "next_action": next_action,
        }

    async def sandbox_node(self, state: AgentState, config: RunnableConfig) -> dict:
        """执行 Python 沙箱环境代码，并将执行结果反馈给 LLM"""
        last_msg = state["messages"][-1]["content"]
        code_match = re.search(r"```python(.*?)```", last_msg, re.DOTALL)
        exec_result = "No executable code block found."

        if code_match:
            code = code_match.group(1).strip()
            on_thinking = config.get("configurable", {}).get("on_thinking")
            if on_thinking:
                await on_thinking(sse("thinking", {"text": f"\n\n[沙箱执行] 正在运行推导代码:\n```python\n{code}\n```\n"}))

            try:
                exec_result = await execute_python_code(code)
            except Exception as e:
                exec_result = f"Error during sandbox execution: {e}"

            if on_thinking:
                await on_thinking(sse("thinking", {"text": f"\n[执行结果]:\n{exec_result}\n继续推理...\n"}))

        user_feedback_msg = {
            "role": "user",
            "content": f"系统后台执行代码结果如下：\n{exec_result}\n请根据结果反思(如果有报错请[CORRECT])，然后继续输出，最终必须以 [OUTPUT] 结束。"
        }

        return {
            "messages": [user_feedback_msg],
            "loop_count": state.get("loop_count", 0) + 1,
        }

    def route_orchestrator(self, state: AgentState) -> str:
        if state.get("loop_count", 0) >= 3:
            return "end"
        return state.get("next_action", "end")

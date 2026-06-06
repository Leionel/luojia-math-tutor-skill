import json
from typing import AsyncIterator

from app.config import Settings
from app.knowledge.search import detect_subject, search_knowledge
from app.llm.openai_compatible import OpenAICompatibleClient
from app.math_tools.step_checker import check_step
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.tutor.intent_router import Intent, route_intent
from app.tutor.prompt_builder import build_messages
from app.memory.mastery import mastery_label, update_mastery
from app.tutor.hint_policy import decide_hint_level, HintLevel


from app.agents.vision_agent import VisionParser
from app.agents.harness_evaluator import PedagogyHarness

def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

class TutorOrchestrator:
    def __init__(self, settings: Settings, repository: Repository):
        self.settings = settings
        self.repository = repository
        self.llm = OpenAICompatibleClient(settings)
        self.skill_text = settings.skill_file.read_text(encoding="utf-8")
        self.vision_parser = VisionParser()
        self.harness = PedagogyHarness(settings)

    async def stream_reply(
        self,
        session_id: str,
        user_id: str,
        message: str,
        subject: str = "auto",
        mode: str = "socratic",
        user_api_key: str | None = None,
        model: str | None = None,
        requested_hint: bool = False,
        image_urls: list[str] | None = None,
    ) -> AsyncIterator[str]:
        self.repository.ensure_user(user_id)
        db_msgs = self.repository.list_messages(session_id)
        history = [{"role": m["role"], "content": m["content"]} for m in db_msgs]

        self.repository.add_message(session_id, "user", message)

        intent = route_intent(message, mode)
        detected_subject = detect_subject(message, subject)
        if detected_subject is None:
            detected_subject = subject
        hits = await search_knowledge(message, detected_subject, limit=5, api_key=user_api_key)

        verifier_result = VerifyResult(False, None, "本轮未触发自动验算。")
        mistake = None
        if intent == Intent.CHECK_STUDENT_STEP or any(key in message for key in ["∫", "\\int", "对吗", "="]):
            verifier_result, mistake = check_step(message)

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
            except Exception:
                pass

        if not concepts:
            concepts = [hit.item.concept_zh for hit in hits[:3] if hit.item.concept_zh]
            if ("∫" in message or "\\int" in message) and "幂函数积分" not in concepts:
                concepts.insert(0, "幂函数积分")
            if mistake and mistake.concept not in concepts:
                concepts.insert(0, mistake.concept)

        if mistake:
            self.repository.add_mistake_event(
                user_id=user_id,
                session_id=session_id,
                subject=detected_subject,
                concept=mistake.concept,
                mistake_code=mistake.code,
            )

        hint_level = 0
        mastery_score = 0.5
        mastery_delta = 0.0
        
        if concepts:
            primary_concept = concepts[0]
            existing_mastery = self.repository.get_mastery(user_id, primary_concept)
            mastery_score = existing_mastery["score"] if existing_mastery else 0.5
            
            if verifier_result.verified and intent == Intent.CHECK_STUDENT_STEP:
                mastery_hint_level = 1 if requested_hint else 0
                result = update_mastery(mastery_score, verifier_result.is_correct, mastery_hint_level)
                mastery_delta = result.delta
                mastery_score = result.new_score
                self.repository.upsert_mastery(user_id, primary_concept, result.new_score, verifier_result.is_correct)
            
            consecutive_errors = self.repository.get_consecutive_errors(user_id, primary_concept)
            hint_level = decide_hint_level(mastery_score, consecutive_errors, requested_hint, mode).value

        mastery_label_str = mastery_label(mastery_score)

        self.repository.add_attempt(
            session_id=session_id,
            user_id=user_id,
            problem_text=message,
            student_step=message if intent == Intent.CHECK_STUDENT_STEP else None,
            is_correct=verifier_result.is_correct,
            mistake_code=mistake.code if mistake else None,
            verifier_summary=verifier_result.summary,
        )

        yield sse(
            "meta",
            {
                "intent": intent.value,
                "subject": detected_subject,
                "concepts": concepts,
                "verified": verifier_result.verified,
                "is_correct": verifier_result.is_correct,
                "mistake": mistake.label if mistake else None,
                "verifier_summary": verifier_result.summary,
                "hint_level": hint_level,
                "mastery_score": mastery_score,
                "mastery_label": mastery_label_str,
                "mastery_delta": mastery_delta,
            },
        )

        yield sse("thinking_start", {"message": "正在思考..."})

        # Feature: If DeepSeek model or pure text logic is preferred, bypass VisionParser because MinerU text is already in the message.
        # But if we must use VisionParser, we can conditionally do it. For MVP v4, we rely on MinerU text.
        
        # Fetch document chunks if session has document_id
        session_data = self.repository.list_sessions(user_id) # actually we just need the single session
        current_session = next((s for s in session_data if s["id"] == session_id), None)
        document_id = current_session.get("document_id") if current_session else None
        
        document_chunks = []
        if document_id:
            yield sse("thinking", {"text": f"[隐式 RAG] 正在检索课件 ({document_id})...\n"})
            document_chunks = self.repository.search_document_chunks(document_id, message, limit=3)

        messages = build_messages(
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

        from app.agents.code_executor import execute_python_code
        import re

        loop_count = 0
        max_loops = 3
        final_output = ""
        thinking_chain = ""

        yield sse("thinking", {"text": "[Orchestrator] 启动 Label-Driven 内部推理闭环...\n"})

        while loop_count < max_loops:
            loop_count += 1
            current_response = ""
            buffer = ""
            in_output = False
            
            async for token in self.llm.stream(messages, api_key=user_api_key, model=model):
                current_response += token
                buffer += token
                
                # Dynamic stream routing
                if not in_output:
                    if "[OUTPUT]" in buffer:
                        in_output = True
                        parts = buffer.split("[OUTPUT]")
                        yield sse("thinking", {"text": parts[0]})
                        thinking_chain += parts[0]
                        if len(parts) > 1 and parts[1]:
                            yield sse("token", {"text": parts[1]})
                            final_output += parts[1]
                        buffer = ""
                    else:
                        # Flush safe part of buffer to thinking (keep last 15 chars to catch split tags)
                        if len(buffer) > 15:
                            safe_chunk = buffer[:-15]
                            buffer = buffer[-15:]
                            yield sse("thinking", {"text": safe_chunk})
                            thinking_chain += safe_chunk
                else:
                    yield sse("token", {"text": buffer})
                    final_output += buffer
                    buffer = ""
                    
            # Flush remaining buffer
            if buffer:
                if not in_output:
                    yield sse("thinking", {"text": buffer})
                    thinking_chain += buffer
                else:
                    yield sse("token", {"text": buffer})
                    final_output += buffer

            # After generation, check if we need to execute code
            if "[VERIFY]" in current_response and "```python" in current_response:
                code_match = re.search(r"```python(.*?)```", current_response, re.DOTALL)
                if code_match:
                    code = code_match.group(1).strip()
                    yield sse("thinking", {"text": f"\n\n[沙箱执行] 正在运行推导代码:\n```python\n{code}\n```\n"})
                    
                    exec_result = await execute_python_code(code)
                    
                    yield sse("thinking", {"text": f"\n[执行结果]:\n{exec_result}\n继续推理...\n"})
                    
                    messages.append({"role": "assistant", "content": current_response})
                    messages.append({
                        "role": "user", 
                        "content": f"系统后台执行代码结果如下：\n{exec_result}\n请根据结果反思(如果有报错请[CORRECT])，然后继续输出，最终必须以 [OUTPUT] 结束。"
                    })
                    continue  # Next loop iteration
            
            # If no code execution triggered, or if [OUTPUT] was reached, break
            if "[OUTPUT]" in current_response or "```python" not in current_response:
                break

        # Note: We skipped PedagogyHarness here to keep the demo simple, 
        # but it could be easily injected here on the final_output if needed.

        yield sse("thinking_end", {"chain": thinking_chain})
        message_id = self.repository.add_message(session_id, "assistant", final_output, intent.value)
        yield sse("done", {"message_id": message_id})

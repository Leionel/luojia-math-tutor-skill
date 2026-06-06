import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.config import get_settings
from app.memory.repository import Repository
from app.tutor.graph import TutorWorkflow, AgentState
from app.tutor.intent_router import Intent
from app.math_tools.verifier import VerifyResult


@pytest.mark.asyncio
async def test_tutor_workflow_compiles():
    settings = get_settings()
    repo = MagicMock(spec=Repository)
    workflow = TutorWorkflow(settings, repo)
    assert workflow.workflow is not None


@pytest.mark.asyncio
async def test_intent_node_checking_step():
    settings = get_settings()
    repo = MagicMock(spec=Repository)
    workflow = TutorWorkflow(settings, repo)

    state: AgentState = {
        "message": "我算 ∫x² dx = x³，对吗？",
        "session_id": "test-session",
        "user_id": "test-user",
        "subject": "calculus",
        "mode": "socratic",
        "user_api_key": None,
        "model": None,
        "requested_hint": False,
        "image_urls": None,
        "messages": [],
        "thinking_steps": []
    }

    result = await workflow.intent_node(state)
    assert result["intent"] == Intent.CHECK_STUDENT_STEP
    assert result["detected_subject"] == "calculus"
    assert result["verifier_result"] is not None
    assert result["verifier_result"].verified is True
    assert result["verifier_result"].is_correct is False
    assert result["mistake"] is not None


@pytest.mark.asyncio
async def test_retrieve_node_initializes_prompt_and_mastery():
    settings = get_settings()
    repo = MagicMock(spec=Repository)
    repo.list_messages.return_value = []
    repo.list_sessions.return_value = []
    repo.get_mastery.return_value = None

    workflow = TutorWorkflow(settings, repo)

    state: AgentState = {
        "message": "什么是导数？",
        "session_id": "test-session",
        "user_id": "test-user",
        "subject": "calculus",
        "mode": "socratic",
        "user_api_key": None,
        "model": None,
        "requested_hint": False,
        "image_urls": None,
        "intent": Intent.CONCEPT,
        "detected_subject": "calculus",
        "verifier_result": VerifyResult(False, None, "未触发"),
        "mistake": None,
        "messages": [],
        "thinking_steps": []
    }

    with patch("app.tutor.graph.search_knowledge", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []
        result = await workflow.retrieve_node(state, config={})
        
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert result["concepts"] == []  # no integral in query, so empty list
        repo.ensure_user.assert_called_once_with("test-user")
        repo.add_message.assert_called_once_with("test-session", "user", "什么是导数？")


@pytest.mark.asyncio
async def test_orchestrator_node_calls_llm_and_streams():
    settings = get_settings()
    repo = MagicMock(spec=Repository)
    workflow = TutorWorkflow(settings, repo)

    state: AgentState = {
        "message": "什么是导数？",
        "session_id": "test-session",
        "user_id": "test-user",
        "subject": "calculus",
        "mode": "socratic",
        "user_api_key": "user-key",
        "model": "model-name",
        "requested_hint": False,
        "image_urls": None,
        "intent": Intent.CONCEPT,
        "detected_subject": "calculus",
        "hits": [],
        "document_chunks": [],
        "verifier_result": None,
        "mistake": None,
        "concepts": [],
        "mastery_score": 0.5,
        "mastery_delta": 0.0,
        "mastery_label_str": "一般",
        "hint_level": 0,
        "messages": [{"role": "system", "content": "system prompt"}],
        "thinking_steps": []
    }

    mock_stream_tokens = ["[PLAN]\nI will explain derivative.\n[OUTPUT]\n导数是函数变化率的极限。"]
    
    async def mock_stream(messages, api_key, model):
        for token in mock_stream_tokens:
            yield token

    with patch.object(workflow.llm, "stream", side_effect=mock_stream):
        on_token = AsyncMock()
        on_thinking = AsyncMock()
        
        config = {
            "configurable": {
                "on_token": on_token,
                "on_thinking": on_thinking
            }
        }
        
        result = await workflow.orchestrator_node(state, config=config)
        
        assert result["final_output"].strip() == "导数是函数变化率的极限。"
        assert "assistant" in result["messages"][0]["role"]
        assert "[PLAN]" in result["messages"][0]["content"]
        assert result["next_action"] == "end"
        
        # Verify callback calls
        on_thinking.assert_called()
        on_token.assert_called()


@pytest.mark.asyncio
async def test_sandbox_node_executes_code():
    settings = get_settings()
    repo = MagicMock(spec=Repository)
    workflow = TutorWorkflow(settings, repo)

    state: AgentState = {
        "message": "calculate 2+2",
        "session_id": "test-session",
        "user_id": "test-user",
        "subject": "calculus",
        "mode": "socratic",
        "user_api_key": None,
        "model": None,
        "requested_hint": False,
        "image_urls": None,
        "intent": Intent.CHECK_STUDENT_STEP,
        "detected_subject": "calculus",
        "hits": [],
        "document_chunks": [],
        "verifier_result": None,
        "mistake": None,
        "concepts": [],
        "mastery_score": 0.5,
        "mastery_delta": 0.0,
        "mastery_label_str": "一般",
        "hint_level": 0,
        "messages": [
            {"role": "user", "content": "calculate 2+2"},
            {"role": "assistant", "content": "Let's check.\n[VERIFY]\n```python\nprint(2+2)\n```\n"}
        ],
        "thinking_steps": [],
        "loop_count": 0,
    }

    with patch("app.tutor.graph.execute_python_code", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "4\n"
        
        result = await workflow.sandbox_node(state, config={})
        
        assert len(result["messages"]) == 1
        assert "4" in result["messages"][0]["content"]
        assert result["loop_count"] == 1
        mock_execute.assert_called_once_with("print(2+2)")

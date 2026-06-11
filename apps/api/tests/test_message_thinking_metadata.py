from app.config import Settings
from app.memory.repository import Repository


def test_message_thinking_metadata_round_trips(tmp_path):
    repository = Repository(
        Settings(database_url=f"sqlite:///{tmp_path / 'messages.db'}")
    )
    session = repository.create_session("user-1", "calculus")

    repository.add_message(
        session["session_id"],
        "assistant",
        "回答",
        "solve_step_by_step",
        "[PLAN]\n识别题型。",
        1250,
    )

    message = repository.list_messages(session["session_id"])[0]
    assert message["thinking_summary"] == "[PLAN]\n识别题型。"
    assert message["thinking_elapsed_ms"] == 1250


def test_message_learning_meta_round_trips(tmp_path):
    repository = Repository(
        Settings(database_url=f"sqlite:///{tmp_path / 'learning-meta.db'}")
    )
    session = repository.create_session("user-1", "linear_algebra")
    learning_meta = {
        "intent": "solve_step_by_step",
        "subject": "linear_algebra",
        "concepts": ["QR 算法", "正交相似变换"],
        "verified": False,
        "is_correct": None,
        "mistake": None,
        "verifier_summary": "本轮无需符号验算。",
        "mastery_score": 0.62,
        "mastery_label": "一般",
        "mastery_delta": 0.0,
        "pedagogical_action": "hint",
        "learning_objective": "理解 QR 迭代",
    }

    repository.add_message(
        session["session_id"],
        "assistant",
        "回答",
        learning_meta=learning_meta,
    )

    message = repository.list_messages(session["session_id"])[0]
    assert message["learning_meta"] == learning_meta


def test_legacy_thinking_summary_restores_learning_meta(tmp_path):
    repository = Repository(
        Settings(database_url=f"sqlite:///{tmp_path / 'legacy-meta.db'}")
    )
    session = repository.create_session("user-1", "linear_algebra")
    repository.add_message(
        session["session_id"],
        "assistant",
        "回答",
        "solve_step_by_step",
        (
            "[PLAN]\n已识别学习目标：理解 QR 迭代；采用教学策略：分步引导。\n\n"
            "[隐式 RAG]\n涉及概念：QR 算法、正交相似变换；已载入会话历史。\n\n"
            "[VERIFY]\n本轮无需自动符号验证。"
        ),
        800,
    )

    message = repository.list_messages(session["session_id"])[0]
    assert message["learning_meta"]["intent"] == "solve_step_by_step"
    assert message["learning_meta"]["concepts"] == [
        "QR 算法",
        "正交相似变换",
    ]
    assert message["learning_meta"]["learning_objective"] == "理解 QR 迭代"
    assert message["learning_meta"]["verified"] is False


def test_legacy_message_content_overrides_noisy_rag_concepts(tmp_path):
    repository = Repository(
        Settings(database_url=f"sqlite:///{tmp_path / 'legacy-content.db'}")
    )
    session = repository.create_session("user-1", "linear_algebra")
    repository.add_message(
        session["session_id"],
        "assistant",
        "QR 算法通过正交相似变换计算对称矩阵的特征值。",
        "full_solution",
        (
            "[PLAN]\n已识别学习目标：理解矩阵迭代。\n\n"
            "[隐式 RAG]\n涉及概念：原假设与备择假设、二项分布置信区间。\n\n"
            "[VERIFY]\n本轮无需自动符号验证。"
        ),
        800,
    )

    message = repository.list_messages(session["session_id"])[0]
    concepts = message["learning_meta"]["concepts"]
    assert concepts[:3] == ["QR 算法", "正交相似变换", "对称矩阵"]
    assert "原假设与备择假设" not in concepts


def test_saved_learning_meta_is_sanitized_by_explicit_content(tmp_path):
    repository = Repository(
        Settings(database_url=f"sqlite:///{tmp_path / 'saved-noise.db'}")
    )
    session = repository.create_session("user-1", "calculus")
    repository.add_message(
        session["session_id"],
        "assistant",
        "Fubini 定理说明二重积分在适当条件下可以交换积分次序。",
        learning_meta={
            "intent": "concept",
            "subject": "calculus",
            "concepts": ["独立同分布的中心极限定理", "数列极限"],
            "verified": False,
            "is_correct": None,
            "mistake": None,
            "verifier_summary": "本轮无需符号验算。",
        },
    )

    message = repository.list_messages(session["session_id"])[0]
    assert message["learning_meta"]["concepts"] == [
        "Fubini 定理",
        "二重积分",
    ]

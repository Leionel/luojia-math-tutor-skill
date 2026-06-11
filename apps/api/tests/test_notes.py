from app.api.routes_notes import GenerateNoteRequest, generate_note
from app.config import Settings
from app.memory.repository import Repository


def test_generated_note_uses_current_session_content(tmp_path):
    repository = Repository(
        Settings(database_url=f"sqlite:///{tmp_path / 'notes.db'}")
    )
    session = repository.create_session(
        "user-1",
        "linear_algebra",
        "对称矩阵特征值",
    )
    session_id = session["session_id"]
    repository.add_message(
        session_id,
        "user",
        "怎么用 QR 算法计算对称矩阵特征值？",
    )
    repository.add_message(
        session_id,
        "assistant",
        "先做 A_k = Q_k R_k，再用 A_{k+1} = R_k Q_k 更新。",
        learning_meta={
            "intent": "full_solution",
            "subject": "linear_algebra",
            "concepts": ["QR 算法", "正交相似变换"],
            "verified": False,
            "is_correct": None,
            "mistake": None,
            "verifier_summary": "本轮无需符号验算。",
            "mastery_score": 0.62,
            "mastery_label": "一般",
            "mastery_delta": 0.0,
            "pedagogical_action": "explain",
            "learning_objective": "理解 QR 迭代",
        },
    )

    note = generate_note(
        GenerateNoteRequest(session_id=session_id),
        repository,
    )["note"]

    assert "QR 算法" in note
    assert "正交相似变换" in note
    assert "怎么用 QR 算法计算对称矩阵特征值" in note
    assert "洛必达" not in note

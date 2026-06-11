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

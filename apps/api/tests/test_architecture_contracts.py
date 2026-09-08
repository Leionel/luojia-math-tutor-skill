import pytest
from fastapi import HTTPException

from app.auth import Principal, decode_token, issue_token, resolve_user_id
from app.config import Settings
from app.memory.repository import Repository
from app.math_tools.verifier import VerifyResult
from app.tutor.intent_router import Intent
from app.tutor.prompt_builder import build_messages


def test_skill_is_the_only_system_prompt():
    messages = build_messages(
        "CANONICAL SKILL",
        "什么是导数？",
        Intent.CONCEPT,
        "calculus",
        [],
        VerifyResult(False, None, "not triggered"),
        None,
        "socratic",
    )
    systems = [item for item in messages if item["role"] == "system"]
    assert systems == [{"role": "system", "content": "CANONICAL SKILL"}]


def test_auth_token_and_cross_user_boundary():
    settings = Settings(
        auth_required=True,
        auth_token_secret="x" * 32,
    )
    token = issue_token("alice", settings)
    assert decode_token(token, settings) == "alice"
    with pytest.raises(HTTPException) as exc:
        resolve_user_id(Principal("alice", True), "bob", settings)
    assert exc.value.status_code == 403


def test_unknown_model_is_an_explicit_configuration_error():
    with pytest.raises(ValueError, match="Unsupported model"):
        Settings().resolve_model("made-up-model")


def test_learning_policy_rejects_uncalibrated_threshold_order():
    with pytest.raises(ValueError, match="thresholds must be ordered"):
        Settings(hint_mastery_formula=0.8, hint_mastery_light=0.2).validate_runtime()


def test_migrations_and_semantic_jobs_are_shared_between_instances(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'shared.db'}")
    first = Repository(settings)
    job_id = first.enqueue_semantic_job("calculus", "求导")
    second = Repository(settings)

    claimed = second.claim_semantic_job()
    assert claimed and claimed["id"] == job_id
    second.complete_semantic_job(job_id, "calculus", "求导", [])
    with first.connect() as connection:
        versions = connection.execute(
            "select version from schema_migrations order by version"
        ).fetchall()
        status = connection.execute(
            "select status from semantic_jobs where id = ?", (job_id,)
        ).fetchone()["status"]
    assert [row["version"] for row in versions] == [1, 2, 3]
    assert status == "done"

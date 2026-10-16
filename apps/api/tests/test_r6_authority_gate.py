"""Real JWT identity matrix and single official publication path."""

import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.config import Settings, get_settings
from app.memory.repository import Repository
from app.main_deps import get_app_settings, get_repository
from app.api import routes_auth, routes_admin_knowledge, routes_courses
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore


def test_legacy_writes_retired_student_denied_teacher_course_path_works(
    tmp_path, monkeypatch
):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path/'auth.db'}",
        auth_required=True,
        teacher_user_ids="teacher-user",
        auth_token_secret="offline-test-secret-01234567890123456789",
    )
    repo = Repository(settings)
    course = CourseService(store=CourseStore(str(tmp_path / "course.db")))
    app = FastAPI()
    for module in (routes_auth, routes_admin_knowledge, routes_courses):
        app.include_router(module.router)
    for dependency, value in [
        (get_app_settings, settings),
        (get_settings, settings),
        (get_repository, repo),
    ]:
        app.dependency_overrides[dependency] = lambda value=value: value
    monkeypatch.setattr(routes_courses, "get_app_settings", lambda: settings)
    monkeypatch.setattr(routes_courses, "get_course_service", lambda _: course)
    output = tmp_path / "legacy-output"
    output.mkdir()
    monkeypatch.setattr(routes_admin_knowledge, "get_output_dir", lambda _: output)
    source = output / "m1_fixture.json"
    source.write_text(
        json.dumps(
            {
                "units": [{"id": "old", "title": "旧资料", "review_status": "pending"}],
                "relations": [],
            }
        ),
        encoding="utf-8",
    )
    before = source.read_bytes()
    with TestClient(app) as client:

        def register(user):
            value = client.post(
                "/api/auth/register",
                json={"user_id": user, "password": "synthetic-passphrase-123"},
            )
            assert value.status_code == 201
            return {"Authorization": "Bearer " + value.json()["access_token"]}

        student = register("student-user")
        assert client.post("/api/auth/register",json={"user_id":"teacher-user","password":"synthetic-passphrase-123"}).status_code==403
        from app.auth import hash_password
        password_hash,salt=hash_password("synthetic-passphrase-123")
        assert repo.create_auth_user("teacher-user","Offline teacher",password_hash,salt)
        login=client.post("/api/auth/login",json={"user_id":"teacher-user","password":"synthetic-passphrase-123"})
        assert login.status_code==200
        teacher={"Authorization":"Bearer "+login.json()["access_token"]}
        assert client.get("/api/admin/knowledge/list").status_code == 401
        assert (
            client.get("/api/admin/knowledge/list", headers=student).status_code == 403
        )
        assert (
            client.get("/api/admin/knowledge/list", headers=teacher).status_code == 200
        )
        calls = [
            ("put", "/api/admin/knowledge/units/old", {"content": "override"}),
            (
                "post",
                "/api/admin/knowledge/review",
                {"unit_ids": ["old"], "action": "approve"},
            ),
            ("post", "/api/admin/knowledge/publish", {}),
        ]
        for method, path, body in calls:
            assert (
                getattr(client, method)(path, headers=student, json=body).status_code
                == 403
            )
            assert (
                getattr(client, method)(path, headers=teacher, json=body).status_code
                == 410
            )
        assert (
            source.read_bytes() == before
            and not (output / "published_knowledge.json").exists()
        )
        candidate = {
            "candidate_id": "R6_GATE_TEST",
            "candidate_type": "new_unit",
            "payload": {
                "id": "R6_GATE_TEST",
                "title": "审核来源测试节点",
                "content": "仅用于离线权限测试。",
                "type": "concept",
            },
            "evidence_ref": "offline-fixture-review",
        }
        assert (
            client.post(
                "/api/courses/numerical_analysis/candidates",
                headers=student,
                json=candidate,
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/courses/numerical_analysis/candidates",
                headers=teacher,
                json=candidate,
            ).status_code
            == 200
        )
        path = "/api/courses/numerical_analysis/candidates/R6_GATE_TEST/review"
        assert (
            client.post(path, headers=student, json={"action": "approve"}).status_code
            == 403
        )
        response = client.post(
            path,
            headers=teacher,
            json={
                "action": "approve",
                "reviewer_id": "spoofed-student",
                "review_note": "离线审核测试",
            },
        )
        assert response.status_code == 200
        receipt = response.json()
        assert receipt["status"] == "success" and receipt["revision_id"]
        assert receipt["candidate"]["reviewer_id"] == "teacher-user"
        data = client.get(
            "/api/courses/numerical_analysis/graph?format=raw", headers=student
        ).json()
        assert any(u["id"] == "R6_GATE_TEST" for u in data["units"])
        assert (
            course.store.list_revisions("numerical_analysis")[-1]["revision_id"]
            == receipt["revision_id"]
        )
        other = register("other-user")
        assert (
            client.get(
                "/api/courses/numerical_analysis/graph?student_id=student-user",
                headers=other,
            ).status_code
            == 403
        )
    course.store.close()

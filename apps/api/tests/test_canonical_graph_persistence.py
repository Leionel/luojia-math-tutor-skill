import json
import sqlite3
from copy import deepcopy

import pytest

from app.knowledge.course_store import CourseStore
from app.knowledge.course_service import CourseService
from app.knowledge.case_repository import TeachingCaseRepository
from app.knowledge.case_schema import TeachingCase


@pytest.fixture
def service(tmp_path):
    svc = CourseService(store=CourseStore(str(tmp_path / "course.db")))
    yield svc
    svc.store.close()


def propose(svc, cid, kind, payload, course="numerical_analysis"):
    return svc.candidate_mgr.add_candidate(cid, kind, course, payload, evidence_ref="document:test:section")


def review(svc, cid, action="approve", **kwargs):
    return svc.review_service.review_candidate(cid, action, reviewer_id="teacher", **kwargs)


def test_all_entities_provenance_and_boundary_survive_new_connection(service, tmp_path):
    propose(service, "u", "new_unit", {"id": "TEST", "title": "测试方法", "source_document_id": "doc",
            "source_span": {"start": 2, "end": 40}, "page_start": 3, "chapter_path": ["求根"], "aliases": ["初始别名"]})
    review(service, "u")
    propose(service, "r", "new_relation", {"source_unit_id": "TEST", "target_unit_id": "NA_NEWTON", "relation_type": "requires"})
    review(service, "r")
    propose(service, "c", "new_case", {"case_id": "TEST_CASE", "title": "测试任务", "concept_ids": ["TEST"], "required_condition_ids": ["NA_NEWTON"]})
    review(service, "c")
    propose(service, "a", "new_alias", {"target_id": "TEST", "alias": "新别名"})
    review(service, "a", "merge")
    propose(service, "v", "new_alias", {"target_id": "TEST_CASE", "variant": "测试问法"})
    review(service, "v", "merge")
    propose(service, "b", "scope_change", {"unit_id": "TEST", "scope_level": "extension"})
    result = review(service, "b")
    expected = service.graph_repo.to_course_pack()
    service.store.close()
    restarted = CourseService(store=CourseStore(str(tmp_path / "course.db")))
    assert restarted.graph_repo.to_course_pack() == expected
    assert restarted.graph_repo.get_unit("TEST").source_span == {"start": 2, "end": 40}
    assert restarted.graph_repo.get_unit("TEST").reviewer_id == "teacher"
    assert restarted.graph_repo.case_repo.get_case("TEST_CASE").accepted_variants == ["测试问法"]
    assert restarted.store.list_revisions("numerical_analysis")[-1]["changed_entities"]["after"] == expected
    assert review(restarted, "b")["revision_id"] == result["revision_id"]
    assert len(restarted.store.list_revisions("numerical_analysis")) == 6
    restarted.store.close()


@pytest.mark.parametrize("kind,payload,action", [
    ("new_unit", {"title": "bad", "scope_level": "unrecognised"}, "approve"),
    ("new_unit", {"id": "NA_NEWTON", "title": "overwrite"}, "approve"),
    ("new_unit", {"title": "bad", "source_span": []}, "approve"),
    ("new_relation", {"source_unit_id": "missing", "target_unit_id": "NA_NEWTON", "relation_type": "requires"}, "approve"),
    ("new_relation", {"source_unit_id": "NA_NEWTON", "target_unit_id": "NA_NEWTON", "relation_type": "unknown"}, "approve"),
    ("new_case", {"case_id": "bad", "title": "bad", "course_id": "other"}, "approve"),
    ("new_case", {"case_id": "bad", "title": "bad", "concept_ids": ["missing"]}, "approve"),
    ("new_alias", {"target_id": "missing", "alias": "bad"}, "merge"),
    ("scope_change", {"unit_id": "NA_NEWTON", "scope_level": "bad"}, "approve"),
    ("unsupported", {"title": "bad"}, "approve"),
])
def test_invalid_review_is_atomic(service, kind, payload, action):
    propose(service, "bad", kind, payload)
    before = deepcopy(service.graph_repo.to_course_pack())
    with pytest.raises(ValueError):
        review(service, "bad", action)
    assert service.graph_repo.to_course_pack() == before
    assert service.store.load_candidates()[0]["status"] == "pending"
    assert not service.store.list_revisions("numerical_analysis")


def test_sqlite_failure_rolls_back_graph_candidate_revision_and_memory(service):
    propose(service, "failure", "new_unit", {"id": "FAILURE", "title": "故障测试"})
    before = service.store.load_graph("numerical_analysis")
    service.store._conn.execute("CREATE TRIGGER fail_revision BEFORE INSERT ON graph_revisions BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        review(service, "failure")
    assert service.store.load_graph("numerical_analysis") == before
    assert service.candidate_mgr.get_candidate("failure").status == "pending"
    assert service.graph_repo.get_unit("FAILURE") is None
    assert service.store.load_candidates()[0]["status"] == "pending"
    assert not service.store.list_revisions("numerical_analysis")
    service.store._conn.execute("DROP TRIGGER fail_revision")
    assert review(service, "failure")["status"] == "success"


def test_seed_change_does_not_overwrite_reviewed_graph(service):
    propose(service, "a", "new_alias", {"target_id": "NA_NEWTON", "alias": "已审别名"})
    review(service, "a", "merge")
    stored = service.store.load_graph("numerical_analysis")
    service.store.initialize_graph("numerical_analysis", {"units": []}, "different_seed")
    assert service.store.load_graph("numerical_analysis") == stored
    with pytest.raises(ValueError, match="already reviewed"):
        review(service, "a", "reject")


def test_foreign_candidate_cannot_be_reviewed(service):
    propose(service, "foreign", "new_unit", {"title": "foreign"}, course="other")
    with pytest.raises(KeyError):
        review(service, "foreign")
    assert service.candidate_mgr.get_candidate("foreign").status == "pending"


def test_stale_generation_cannot_commit(service):
    candidate = propose(service, "race", "new_unit", {"title": "race"}).to_dict()
    graph = service.store.load_graph("numerical_analysis")
    service.store._conn.execute("UPDATE canonical_graphs SET generation=generation+1")
    service.store._conn.commit()
    with pytest.raises(ValueError, match="Graph changed"):
        service.store.commit_review(candidate, {**candidate, "status": "approved"}, graph["data"], graph["generation"], {})
    assert service.store.load_candidates()[0]["status"] == "pending"


def test_backup_restores_reviewed_state(service, tmp_path):
    propose(service, "backup", "new_unit", {"id": "RESTORED", "title": "备份恢复"})
    review(service, "backup")
    with sqlite3.connect(tmp_path / "backup.db") as backup:
        service.store._conn.backup(backup)
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    restored = CourseService(store=CourseStore(str(tmp_path / "backup.db")))
    assert restored.graph_repo.get_unit("RESTORED") is not None
    assert restored.candidate_mgr.get_candidate("backup").status == "approved"
    restored.store.close()


def test_case_indexes_exclude_other_courses_and_old_anchors():
    repo = TeachingCaseRepository([TeachingCase("c", "a", "title", concept_ids=["old"])])
    repo.add_case(TeachingCase("c", "b", "title", concept_ids=["new"]))
    assert repo.list_cases(course_id="a") == []
    assert repo.list_cases(course_id="absent") == []
    assert repo.find_by_concept("old") == []
    assert repo.find_by_concept("new")[0].course_id == "b"


def test_candidate_course_collision_does_not_modify_original(service):
    propose(service, "collision", "new_unit", {"title": "original"})
    before = service.store.load_candidates()
    with pytest.raises(ValueError, match="another course"):
        propose(service, "collision", "new_unit", {"title": "other"}, course="other")
    assert service.store.load_candidates() == before


def test_maintenance_copy_and_no_overwrite(service, tmp_path):
    import importlib.util
    from pathlib import Path
    module_path = Path(__file__).resolve().parents[3] / "scripts/course_store_maintenance.py"
    spec = importlib.util.spec_from_file_location("course_maintenance", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    propose(service, "maint", "new_unit", {"id": "MAINT", "title": "维护恢复"})
    review(service, "maint")
    source, destination = tmp_path / "course.db", tmp_path / "restored.db"
    result = module.copy_database(source, destination)
    assert result["integrity"] == "ok"
    assert result["candidate_status_counts"] == {"approved": 1}
    with pytest.raises(ValueError, match="overwrite"):
        module.copy_database(source, destination)
    restored = CourseService(store=CourseStore(str(destination)))
    assert restored.graph_repo.get_unit("MAINT") is not None
    restored.store.close()

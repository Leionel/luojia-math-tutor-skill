"""R6.2 persisted counterexamples. Fixtures establish orchestration, not pedagogy gains."""
import json
from copy import deepcopy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import routes_explorations
from app.auth import Principal, get_principal
from app.main_deps import get_learning_workspace
from app.tutor.explorations import Explorations, Create, EditGraph, PersonalGraph, SaveAdvice, RelationDecision, Execute, Revise
from app.tutor.personal_recall import select_personal_context, validate_personal_context
from app.tutor.learning_workspace import LearningWorkspace, digest
from app.knowledge.course_store import CourseStore
from app.knowledge.course_service import CourseService
from app.tutor.teaching_decision import source_bundle
from test_learning_workspace import workspace


def seed(w, id="old", source=None):
    w.repository.ensure_user("alice")
    s=Explorations(w)
    s.create("alice",Create(request_id=id,title="Newton初值探索",claim="Newton任意初值都能收敛"))
    graph={"nodes":[{"id":"initial","label":"初值","source_ref":source},{"id":"converge","label":"Newton收敛"}],
           "edges":[{"id":"edge","source":"initial","target":"converge","relation":"implies","reason":"之前认为任意初值都可收敛"}]}
    v=s.update("alice",id,"graph",EditGraph(request_id="graph",expected_revision=1,graph=PersonalGraph.model_validate(graph)))
    v=s.update("alice",id,"run",Execute(request_id="run",expected_revision=2,
        tasks=[{"domain":"root_finding","method":"newton","function":"x^3-2*x+2","initial_value":0,"limit":6}],prediction="会收敛",metrics=["residual"],confirmed=True))
    return s.update("alice",id,"revise",Revise(request_id="revise",expected_revision=3,claim="Newton并非任意初值都收敛",reason="保存的初值0轨迹重复0与1"))


def test_relevant_unrelated_stale_and_user_isolation_from_reopened_store(workspace):
    seed(workspace)
    selected=select_personal_context(workspace,"alice","Newton 换初值还需要什么条件？")
    assert len(selected)==1 and selected[0]["relation_id"]=="edge"
    assert selected[0]["original_claim"]!=selected[0]["current_claim"]
    assert selected[0]["experiments"][0]["rows"][0]["x"]==0
    assert "初值" in selected[0]["next_question"] and selected[0]["relation_version"]
    assert select_personal_context(workspace,"alice","Simpson 积分误差估计能当误差界吗？")==[]
    assert select_personal_context(workspace,"alice","GS 的初值怎样影响残差？")==[]
    assert select_personal_context(workspace,"bob","Newton 换初值还需要什么条件？")==[]
    path=workspace.store._query("PRAGMA database_list")[0][2]
    reopened=CourseStore(path)
    w=LearningWorkspace(CourseService(store=reopened),workspace.repository)
    assert select_personal_context(w,"alice","Newton 换初值还需要什么条件？")==selected
    reopened.close()
    assert workspace.repository.list_mastery("alice")==[]
    assert source_bundle({"message":"新问题","personal_context":selected})["sources"][1]["kind"]=="personal_judgment"
    value=Explorations(workspace).get("alice","old");value["schema_version"]="unsupported-future-version"
    workspace.save("alice","exploration","old",value)
    assert select_personal_context(workspace,"alice","Newton 换初值还需要什么条件？")==[]


def test_changed_source_is_omitted_and_existing_selection_fails_closed(workspace):
    workspace.repository.ensure_user("alice")
    session=workspace.repository.create_session("alice","数学")["session_id"]
    note_id=workspace.repository.save_note("alice",session,"初值条件","原始条件")
    note=next(n for n in workspace.repository.list_notes("alice") if n["id"]==note_id)
    # Repository returns a note object; use its durable identity and exact content hash.
    ref={"kind":"note","note_id":note["id"],"source_hash":digest(note["content"])}
    seed(workspace,source=ref)
    selected=select_personal_context(workspace,"alice","Newton 换初值有什么影响？")
    assert selected and selected[0]["evidence_refs"][0]["ref"]==ref
    with workspace.repository.connect() as conn:
        conn.execute("update notes set content=? where id=?",("已改写条件",note["id"]))
    assert select_personal_context(workspace,"alice","Newton 换初值有什么影响？")==[]
    with pytest.raises(ValueError):validate_personal_context(workspace,"alice",selected)


def test_changed_selected_run_does_not_fall_back_to_another_old_run(workspace):
    seed(workspace)
    s=Explorations(workspace)
    v=s.update("alice","old","run",Execute(request_id="run2",expected_revision=4,
        tasks=[{"domain":"root_finding","method":"newton","function":"x^3-2*x+2","initial_value":-2,"limit":6}],prediction="可能残差达标",metrics=["residual"],confirmed=True))
    latest=v["runs"][-1]
    saved=workspace.get("alice","lab",latest["record_id"]);saved["input_hash"]="0"*64
    workspace.save("alice","lab",saved["id"],saved)
    selected=select_personal_context(workspace,"alice","Newton 初值如何影响收敛？")
    assert selected and not selected[0]["experiments"]
    assert selected[0]["unavailable_experiments"][0]["ref"]==latest


def test_pending_edit_accept_reject_receipts_revision_and_no_official_write(workspace):
    seed(workspace)
    s=Explorations(workspace)
    graph=deepcopy(s.get("alice","old")["graph"])
    v=s.update("alice","old","advice",SaveAdvice(request_id="advice",expected_revision=4,advice={"suggested_graph":graph}))
    c=v["relation_candidates"][0]
    assert c["status"]=="pending"
    assert all(x["relation_id"]!=c["id"] for x in select_personal_context(workspace,"alice","Newton 初值条件"))
    graph["edges"][0]["relation"]="challenges"
    graph["edges"][0]["reason"]="初值0的循环质疑全局猜测"
    v=s.update("alice","old","relation_decision",RelationDecision(request_id="edit",expected_revision=5,candidate_id=c["id"],candidate_version=1,decision="edit",reason="修正方向",graph=graph))
    assert v["relation_candidates"][0]["version"]==2
    with pytest.raises(ValueError):s.update("alice","old","relation_decision",RelationDecision(request_id="stale",expected_revision=6,candidate_id=c["id"],candidate_version=1,decision="accept",reason="过期"))
    before=workspace.store.load_graph(workspace.course_id)
    body=RelationDecision(request_id="accept",expected_revision=6,candidate_id=c["id"],candidate_version=2,decision="accept",reason="仅作私人确认")
    v=s.update("alice","old","relation_decision",body)
    assert s.update("alice","old","relation_decision",body)["revision"]==7
    assert v["decision_receipts"]["accept"]["status"]=="accepted"
    assert v["graph"]["edges"][-1]["relation"]=="challenges"
    assert workspace.store.load_graph(workspace.course_id)==before
    v=s.update("alice","old","advice",SaveAdvice(request_id="advice2",expected_revision=7,advice={"suggested_graph":graph}))
    c=v["relation_candidates"][-1]
    v=s.update("alice","old","relation_decision",RelationDecision(request_id="reject",expected_revision=8,candidate_id=c["id"],candidate_version=1,decision="reject",reason="依据不足"))
    assert v["decision_receipts"]["reject"]["status"]=="rejected" and len(v["graph"]["edges"])==2
    app=FastAPI();app.include_router(routes_explorations.router)
    app.dependency_overrides[get_learning_workspace]=lambda:workspace
    app.dependency_overrides[get_principal]=lambda:Principal("bob",True)
    with TestClient(app) as client:
        assert client.post("/api/explorations/old/relations/decision",json=body.model_dump()).status_code==404


@pytest.mark.asyncio
async def test_new_chat_with_without_context_captures_selection_and_behavior(workspace,monkeypatch,tmp_path):
    from app.config import Settings
    from app.tutor.orchestrator import TutorOrchestrator
    from test_orchestrator import parse_event
    seed(workspace)
    tutor=TutorOrchestrator(Settings(database_url=f"sqlite:///{workspace.repository.db_path}"),workspace.repository)
    workflow=tutor.workflow_owner
    async def no_hits(*args,**kwargs):return None
    monkeypatch.setattr(workflow.context_collector,"_course_graph_pack",no_hits)
    monkeypatch.setattr(workflow.context_collector,"_budgeted_local_pack",no_hits)
    prompts=[]
    async def model(messages,*args,**kwargs):
        text="\n".join(m["content"] for m in messages);prompts.append(text)
        has_personal='"personal_context"' in text
        answer="你曾把任意初值与Newton收敛相联系，后来因0与1循环而修订。现在换初值时，你能说明本题满足哪些局部收敛条件吗？ [personal:0]" if has_personal else "请给出函数、初值与需要检查的收敛条件。"
        d={"claim_ref":"claim:current","evidence_refs":["claim:current",*(["personal:0"] if has_personal else [])],"known_conditions":[],"missing_conditions":["本题局部收敛条件"],"claim_status":"unknown","action":"ask_missing_condition","disclosure":"scaffolded","reason":answer,"assessments":[],"experiment_proposal":None}
        return "[TEACHING_DECISION]"+json.dumps(d,ensure_ascii=False)+"[/TEACHING_DECISION][OUTPUT]"+answer
    monkeypatch.setattr(workflow,"_collect_model_response",model)
    evidence=[]
    for enabled in (False,True):
        session=workspace.repository.create_session("alice","新一轮问题")["session_id"]
        events=[parse_event(e) async for e in tutor.stream_reply(session,"alice","什么是Newton局部收敛条件？换初值时如何理解？",learning_workspace=workspace if enabled else None)]
        assert any(n=="done" for n,_ in events)
        saved=workspace.repository.list_messages(session)[-1]
        evidence.append({"with_personal_context":enabled,"selected":saved["learning_meta"].get("personal_context",[]),"decision":saved["learning_meta"].get("teaching_decision"),"behavior":saved["content"],"validation":"fixture_orchestration_not_teaching_quality"})
    assert not evidence[0]["selected"] and evidence[1]["selected"]
    assert evidence[1]["decision"]["status"]=="accepted" and "personal:0" in evidence[1]["decision"]["evidence_refs"]
    assert "0与1循环" in evidence[1]["behavior"] and evidence[0]["behavior"]!=evidence[1]["behavior"]
    assert '"personal_context"' not in prompts[0] and '"personal_context"' in prompts[-1]
    report=tmp_path/"comparison.json";report.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    import os
    if os.environ.get("LUOJIA_R62_REPORT"):
        from pathlib import Path
        Path(os.environ["LUOJIA_R62_REPORT"]).write_text(report.read_text(encoding="utf-8"),encoding="utf-8")

"""R6.1 integration contracts. Model fixtures check wiring, never model quality."""
import json
from copy import deepcopy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import routes_explorations, routes_tutor
from app.auth import Principal, get_principal
from app.config import Settings
from app.main_deps import get_learning_workspace, get_app_settings
from app.tutor.explorations import Explorations, Create, Execute, EditGraph, PersonalGraph, Revise, AdviceFeedback, proposal
from app.tutor.exploration_advice import advise, AdviceRequest
from app.tutor.learning_context import ExplorationContextRef, resolve_learning_context
from app.tutor.teaching_decision import source_bundle
from app.llm.openai_compatible import OpenAICompatibleClient
from test_learning_workspace import workspace


def create(w, claim="Newton 对 x^3-2*x+2 从0开始为什么循环？"):
    w.repository.ensure_user("alice")
    return Explorations(w).create("alice", Create(request_id="exp", title="数学探索", claim=claim))


def fixture_advice(domain="root_finding", claim="Newton 对 x^3-2*x+2 从0开始为什么循环？"):
    tasks = [dict(domain="root_finding", method="newton", function="x^3-2*x+2", initial_value=x, limit=12) for x in (0, -2)] if domain=="root_finding" else proposal()["tasks"]
    return {"decision":{"claim_ref":"claim:current", "evidence_refs":["claim:current"],
                        "known_conditions":["已给函数和初值"],"missing_conditions":["全局收敛条件"],
                        "claim_status":"unknown","action":"offer_experiment","disclosure":"scaffolded",
                        "reason":"对比两个初值的有限轨迹，再检查局部收敛条件", "assessments":[],
                        "experiment_proposal":{"claim_to_test":claim,"known_conditions":["指定的参数"],"varying_factors":["initial_value"] if domain=="root_finding" else ["matrix"],"fixed_factors":["method","tolerance"],"mathematical_reason":"保持其他因素，比较参数对有限轨迹的影响","tool_limitations":["有限计算不能证明一般收敛"],"question_to_test":"初值对轨迹的影响", "changed_parameter":"task_parameters", "tasks":tasks,"observable":"迭代值、残差与相邻步变化"}},
            "suggested_graph":{"nodes":[{"id":"initial","label":"初值"},{"id":"convergence","label":"收敛"}],"edges":[{"id":"e","source":"initial","target":"convergence","relation":"related","reason":"不同初值可能改变收敛行为"}]},
            "follow_up":"先核对0→1→0是否重复，再比较负初值的残差。有限实验不能证明全局收敛。"}


@pytest.mark.asyncio
async def test_model_suggestion_edit_execute_graph_revision_and_chat_context(workspace,monkeypatch):
    domain="root_finding"
    service=Explorations(workspace)
    value=create(workspace)
    captured=[]
    async def model(self,messages,**kwargs):
        assert kwargs["effort"]=="off"
        captured.append(json.loads(messages[-1]["content"])["context"])
        result=fixture_advice(domain, captured[-1]["student_claim"]["text"])
        if captured[-1].get("teaching_focus"):
            result["decision"]["evidence_refs"].append("context:personal_relations")
            result["decision"]["reason"]=captured[-1]["teaching_focus"]["question"]
        return json.dumps(result,ensure_ascii=False)
    monkeypatch.setattr(OpenAICompatibleClient,"chat_completion",model)
    settings=Settings(llm_api_key="fixture-only")
    advice=await advise(workspace,"alice","exp",AdviceRequest(expected_revision=1),settings)
    assert advice["status"]=="suggested_not_executed"
    value=advice["exploration"]
    assert value["revision"]==2 and value["runs"]==[]
    assert not workspace.store.learning_records("alice",workspace.course_id,"lab")
    tasks=deepcopy(advice["decision"]["experiment_proposal"]["tasks"])
    tasks[0]["limit"]=8  # student editing happens before execution
    value=service.update("alice","exp","run",Execute(request_id="run",expected_revision=2,tasks=tasks,prediction="比较初值和残差",metrics=["residual","step"],confirmed=True))
    assert len(value["runs"])==2
    if domain=="root_finding":
        saved=workspace.get("alice","lab",value["runs"][0]["record_id"])
        assert [r["x"] for r in saved["rows"][:3]]==[0,1,0]
    graph=PersonalGraph.model_validate(advice["suggested_graph"])
    value=service.update("alice","exp","graph",EditGraph(request_id="graph",expected_revision=3,graph=graph))
    value=service.update("alice","exp","revise",Revise(request_id="revision",expected_revision=4,claim="有限轨迹不能推出全局结论",reason="对照了两个初值"))
    ref=ExplorationContextRef(kind="exploration",record_id="exp",revision=5)
    context=resolve_learning_context(workspace,"alice",ref)
    assert context["original_claim"]!=context["student_claim"]["text"]
    assert len(context["experiments"])==2 and context["personal_relations"]["edges"]==graph.model_dump()["edges"]
    assert "context:personal_relations" in {s["id"] for s in source_bundle({"learning_context":context})["sources"]}
    subsequent=await advise(workspace,"alice","exp",AdviceRequest(expected_revision=5),settings)
    assert "初值" in subsequent["decision"]["reason"]
    assert "context:personal_relations" in subsequent["decision"]["evidence_refs"]
    assert captured[-1]["revisions"][0]["claim"]=="有限轨迹不能推出全局结论"
    assert captured[-1]["personal_relations"]["edges"][0]["reason"]==graph.edges[0].reason
    assert workspace.repository.list_mastery("alice")==[]


@pytest.mark.asyncio
async def test_model_missing_tools_and_unavailable_never_fakes_execution(workspace,monkeypatch):
    create(workspace,"任意连续函数都可以证明解析解吗？")
    assert (await advise(workspace,"alice","exp",AdviceRequest(expected_revision=1),Settings(llm_api_key="")))["status"]=="unavailable"
    data=fixture_advice();data["decision"].update(action="ask_missing_condition",experiment_proposal=None)
    data["suggested_graph"]={"nodes":[],"edges":[]}
    async def model(*args,**kwargs):return json.dumps(data)
    monkeypatch.setattr(OpenAICompatibleClient,"chat_completion",model)
    reply=await advise(workspace,"alice","exp",AdviceRequest(expected_revision=1),Settings(llm_api_key="fixture-only"))
    assert reply["decision"]["experiment_proposal"] is None and not reply["exploration"]["runs"]
    data["decision"]["evidence_refs"]=["invented:theorem"]
    bad=await advise(workspace,"alice","exp",AdviceRequest(expected_revision=2),Settings(llm_api_key="fixture-only"))
    assert bad["status"]=="unavailable" and Explorations(workspace).get("alice","exp")["revision"]==2


def test_http_chat_seed_identity_revision_restore_and_newton_tampering(workspace):
    app=FastAPI();app.include_router(routes_explorations.router);app.include_router(routes_tutor.router)
    app.dependency_overrides[get_learning_workspace]=lambda:workspace
    app.dependency_overrides[get_principal]=lambda:Principal("alice",True)
    session=workspace.repository.create_session("alice","数学")["session_id"]
    workspace.repository.add_message(session,"user","Newton 初值会循环吗？")
    with TestClient(app) as client:
        seed=client.get(f"/api/explorations/from-chat/{session}").json()
        assert seed["claim"]=="Newton 初值会循环吗？"
        value=client.post("/api/explorations",json={**seed,"request_id":"exp"}).json()
        assert value["linked_chats"][0]["id"]==session
        tasks=fixture_advice()["decision"]["experiment_proposal"]["tasks"]
        value=client.post("/api/explorations/exp/runs",json={"request_id":"run","expected_revision":1,"tasks":tasks,"metrics":["residual"],"confirmed":True,"prediction":"两个初值可能不同"}).json()
        ref={"kind":"exploration","record_id":"exp","revision":2}
        assert client.post("/api/tutor/context",json=ref).status_code==200
        assert client.post("/api/tutor/context",json={**ref,"revision":1}).status_code==409
        run=workspace.get("alice","lab",value["runs"][0]["record_id"]);run["rows"][1]["x"]=100
        workspace.save("alice","lab",run["id"],run)
        assert client.post("/api/tutor/context",json=ref).status_code==409
        app.dependency_overrides[get_principal]=lambda:Principal("bob",True)
        assert client.get(f"/api/explorations/from-chat/{session}").status_code==404
        assert client.post("/api/tutor/context",json=ref).status_code==404


def test_reject_and_structured_parameter_validation(workspace):
    create(workspace)
    value=Explorations(workspace).update("alice","exp","reject_relation",AdviceFeedback(request_id="reject",expected_revision=1,reason="缺少逻辑依据"))
    assert value["history"][-1]["payload"]["reason"]=="缺少逻辑依据"
    bad=fixture_advice()["decision"]["experiment_proposal"]["tasks"]
    bad[0]["function"]="__import__('os')"
    with pytest.raises(ValueError):Execute(request_id="bad",expected_revision=2,tasks=bad,prediction="观察",confirmed=True,metrics=["residual"])


def test_r6_pending_creation_can_replay_after_optional_chat_origin_is_added(workspace):
    from app.tutor.learning_workspace import digest
    value=create(workspace)
    body=Create(request_id="exp",title=value["title"],claim=value["claim"])
    value["create_hash"]=digest(body.model_dump(exclude_none=True))
    workspace.save("alice","exploration","exp",value)
    assert Explorations(workspace).create("alice",body)["revision"]==1


@pytest.mark.asyncio
@pytest.mark.parametrize("failure",["action_mismatch","dangling_candidate"])
async def test_live_response_contract_failures_are_not_delivered_as_ready_experiments(workspace,monkeypatch,failure):
    create(workspace)
    data=fixture_advice()
    if failure=="action_mismatch":data["decision"]["action"]="ask_missing_condition"
    else:data["suggested_graph"]["nodes"].pop()
    async def model(*args,**kwargs):return json.dumps(data)
    monkeypatch.setattr(OpenAICompatibleClient,"chat_completion",model)
    result=await advise(workspace,"alice","exp",AdviceRequest(expected_revision=1),Settings(llm_api_key="fixture-only"))
    assert result["status"]==("unavailable" if failure=="action_mismatch" else "suggested_not_executed")
    assert Explorations(workspace).get("alice","exp")["runs"]==[]
    assert Explorations(workspace).get("alice","exp")["revision"]==(1 if failure=="action_mismatch" else 2)
    if failure=="dangling_candidate":assert result["candidate_warning"] and not result["suggested_graph"]["edges"]


@pytest.mark.asyncio
async def test_exploration_context_reaches_existing_chat_runtime_and_saved_session(workspace,monkeypatch):
    from app.tutor.orchestrator import TutorOrchestrator
    from test_orchestrator import parse_event
    value=create(workspace)
    service=Explorations(workspace)
    graph=PersonalGraph.model_validate(fixture_advice()["suggested_graph"])
    value=service.update("alice","exp","graph",EditGraph(request_id="graph",expected_revision=1,graph=graph))
    value=service.update("alice","exp","run",Execute(request_id="run",expected_revision=2,
        tasks=fixture_advice()["decision"]["experiment_proposal"]["tasks"],prediction="负初值可能收敛",metrics=["residual"],confirmed=True))
    value=service.update("alice","exp","revise",Revise(request_id="revision",expected_revision=3,claim="不是任意初值都收敛",reason="初值0循环，而-2趋向负根"))
    session=workspace.repository.create_session("alice","数学")["session_id"]
    tutor=TutorOrchestrator(Settings(database_url=f"sqlite:///{workspace.repository.db_path}"),workspace.repository)
    workflow=tutor.workflow_owner
    async def no_hits(*args,**kwargs):return None
    monkeypatch.setattr(workflow.context_collector,"_course_graph_pack",no_hits)
    monkeypatch.setattr(workflow.context_collector,"_budgeted_local_pack",no_hits)
    prompts=[]
    async def model(messages,*args,**kwargs):
        prompts.append(messages)
        return "你已修订为不是任意初值都收敛。结合已保存的初值与收敛关系，下一步检查局部收敛条件；有限轨迹不证明一般结论。"
    monkeypatch.setattr(workflow,"_collect_model_response",model)
    ref=ExplorationContextRef(kind="exploration",record_id="exp",revision=4,selected_run_id=value["runs"][0]["record_id"])
    events=[parse_event(e) async for e in tutor.stream_reply(session,"alice","我现在的关系依据还缺什么条件？",learning_context=ref,learning_workspace=workspace)]
    assert any(name=="done" for name,_ in events)
    prompt="\n".join(m["content"] for turn in prompts for m in turn)
    assert all(word in prompt for word in ("original_claim","teaching_focus","不是任意初值都收敛","personal_relations","experiments"))
    saved=workspace.repository.list_messages(session)[-1]["learning_meta"]
    assert saved["learning_context"]["ref"]==ref.model_dump()
    assert saved["mastery_delta"]==0 and not saved["verified"] and saved["is_correct"] is None
    assert service.view("alice",service.get("alice","exp"))["linked_chats"][0]["id"]==session
    assert resolve_learning_context(workspace,"alice",ExplorationContextRef(**saved["learning_context"]["ref"]))["teaching_focus"]["relation_id"]=="e"

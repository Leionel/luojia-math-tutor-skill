"""Three real runner verticals, edited fixture plans and persistent revisions."""
import json
from copy import deepcopy
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import routes_explorations, routes_tutor
from app.auth import Principal, get_principal
from app.config import Settings
from app.main_deps import get_learning_workspace, get_app_settings
from app.math_tools.exploration_tasks import ExperimentPlan
from app.math_tools.numerical_lab import IntegrationTask, run_numerical
from app.tutor.explorations import Explorations, Create, Execute
from app.tutor.exploration_advice import advise, AdviceRequest
from app.tutor.learning_context import resolve_learning_context, ExplorationContextRef
from app.llm.openai_compatible import OpenAICompatibleClient
from test_learning_workspace import workspace

ROOT=Path(__file__).resolve().parents[3]
CASES=json.loads((ROOT/"evaluation/r63/cases.json").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case",CASES,ids=lambda c:c["id"])
def test_controlled_api_vertical_real_math_prediction_revision_restore_and_reference(workspace,case,tmp_path):
    app=FastAPI();app.include_router(routes_explorations.router);app.include_router(routes_tutor.router)
    app.dependency_overrides[get_learning_workspace]=lambda:workspace
    app.dependency_overrides[get_principal]=lambda:Principal("alice",True)
    plan=deepcopy(case["plan"])
    # Student edits the common budget, keeping the declared comparison intact.
    for t in plan["tasks"]:t["limit"]+=1
    with TestClient(app) as client:
        v=client.post("/api/explorations",json={"request_id":case["id"],"title":case["id"],"claim":case["claim"]}).json()
        body={"request_id":"execute","expected_revision":1,"tasks":plan["tasks"],"plan":plan,"prediction":case["prediction"],"confirmed":True,"metrics":["error_estimate"] if case["id"]=="integration" else ["residual"]}
        assert client.post(f"/api/explorations/{case['id']}/runs",json={**body,"confirmed":False}).status_code==422
        reply=client.post(f"/api/explorations/{case['id']}/runs",json=body)
        assert reply.status_code==200,reply.text
        v=reply.json();event=v["history"][-1]
        assert len(v["runs"])==2 and event["payload"]["plan"]["tasks"]==event["payload"]["confirmed_tasks"]
        assert event["payload"]["prediction"]==case["prediction"]
        assert client.post(f"/api/explorations/{case['id']}/runs",json=body).json()["revision"]==2
        runs=event["payload"]["runs"]
        if case["id"]=="gs":
            assert runs[1]["matrix_evidence"]["spectral_radius_exact"]=="1/5"
            assert not runs[1]["matrix_evidence"]["strict_row_dominant"]
        elif case["id"]=="newton":
            assert [r["x"] for r in runs[0]["rows"][:4]]==[0,1,0,1]
            assert abs(runs[1]["rows"][-1]["fx"])<=1e-6
        else:
            a,b=[r["rows"][-1] for r in runs]
            assert abs(b["value"]-0.2)<abs(a["value"]-0.2)
            assert a["error_bound"] is None and b["error_bound"] is None
        v=client.post(f"/api/explorations/{case['id']}/claim",json={"request_id":"revise","expected_revision":2,"claim":case["revised_claim"],"reason":case["revision_reason"]}).json()
        ref={"kind":"exploration","record_id":case["id"],"revision":3,"selected_run_id":v["runs"][0]["record_id"]}
        ctx=client.post("/api/tutor/context",json=ref)
        assert ctx.status_code==200,ctx.text
        assert ctx.json()["original_claim"]==case["claim"] and len(ctx.json()["experiments"])==2
        assert client.get(f"/api/explorations/{case['id']}").json()["history"][1]["payload"]["prediction"]==case["prediction"]
        app.dependency_overrides[get_principal]=lambda:Principal("bob",True)
        assert client.post("/api/tutor/context",json=ref).status_code==404
    assert not workspace.repository.list_mastery("alice")
    import os
    if os.environ.get("LUOJIA_R63_REPORT_DIR"):
        out=Path(os.environ["LUOJIA_R63_REPORT_DIR"]);out.mkdir(parents=True,exist_ok=True)
        (out/f"{case['id']}.json").write_text(json.dumps({"case":case,"edited_plan":plan,"actual_runs":runs,"restored":v,"context":ctx.json(),"model_evidence":"fixture_orchestration_only"},ensure_ascii=False,indent=2),encoding="utf-8")


def test_aliasing_counterexample_estimate_does_not_bound_true_error(workspace):
    # Smooth nonnegative function, integral 1/2; nested n=4,8 grids alias its oscillation.
    task=IntegrationTask(method="simpson",expression="sin(8*pi*x)^2",left=0,right=1,intervals=4,tolerance=1e-6,limit=2)
    result=run_numerical(task);last=result["rows"][-1]
    assert result["status"]=="estimated_tolerance_met" and last["error_estimate"]<1e-6
    assert abs(last["value"]-0.5)>0.49 and last["error_bound"] is None
    assert result["evidence_scope"]=="quadrature_error_estimate"


@pytest.mark.asyncio
async def test_integration_plan_reaches_shared_advice_without_execution(workspace,monkeypatch):
    case=CASES[2]
    from test_exploration_advice import fixture_advice
    Explorations(workspace).create("alice",Create(request_id="exp",title="共享流程",claim=case["claim"]))
    captured=[]
    async def model(self,messages,**kwargs):
        data=json.loads(messages[-1]["content"]);captured.append(data)
        response=fixture_advice(claim=case["claim"]);response["decision"]["experiment_proposal"]=case["plan"]
        return json.dumps(response,ensure_ascii=False)
    monkeypatch.setattr(OpenAICompatibleClient,"chat_completion",model)
    result=await advise(workspace,"alice","exp",AdviceRequest(expected_revision=1),Settings(llm_api_key="offline-fixture"))
    assert result["status"]=="suggested_not_executed",result
    assert result["decision"]["experiment_proposal"]["tasks"][0]["domain"]==case["plan"]["tasks"][0]["domain"]
    assert not result["exploration"]["runs"]
    assert all(domain in json.dumps(captured[0]["schema"]) for domain in ("linear_system","root_finding","integration"))




def test_plan_tampering_domain_bounds_and_failed_run_atomicity(workspace):
    plan=deepcopy(CASES[2]["plan"])
    plan["tasks"][1]["left"]=0.1
    with pytest.raises(ValueError):ExperimentPlan.model_validate(plan)
    plan=deepcopy(CASES[2]["plan"]);plan["tasks"][1]=CASES[1]["plan"]["tasks"][1]
    with pytest.raises(ValueError):ExperimentPlan.model_validate(plan)
    for expression in ("__import__('os')","open('secrets')","x.__class__"):
        with pytest.raises(ValueError):Execute(request_id="run",expected_revision=1,tasks=[{**CASES[2]["plan"]["tasks"][0],"expression":expression}],prediction="未知",metrics=["value"],confirmed=True)
    s=Explorations(workspace);s.create("alice",Create(request_id="exp",title="定义域",claim="比较积分"))
    tasks=deepcopy(CASES[2]["plan"]["tasks"]);tasks[1]["expression"]="1/(x-0.5)"
    with pytest.raises(ValueError):s.update("alice","exp","run",Execute(request_id="bad",expected_revision=1,tasks=tasks,prediction="未知",metrics=["value"],confirmed=True))
    assert not s.get("alice","exp")["runs"] and not workspace.store.learning_records("alice",workspace.course_id,"numerical_lab")
    # R6/R6.1 pending retries predate optional plan fields; preserve their receipt identity.
    from app.tutor.learning_workspace import digest
    body=Execute(request_id="legacy",expected_revision=1,tasks=CASES[2]["plan"]["tasks"],prediction="旧客户端的预测",metrics=["value"],confirmed=True)
    v=s.update("alice","exp","run",body)
    v["receipts"]["legacy"]=digest({"action":"run","body":body.model_dump(exclude={"plan","plan_origin"})})
    workspace.save("alice","exploration","exp",v)
    assert s.update("alice","exp","run",body)["revision"]==2

from copy import deepcopy
import json
import pytest
from app.tutor.learning_context import IntegrationContextRef, resolve_learning_context
from app.math_tools.numerical_lab import IntegrationTask, run_numerical
from app.tutor.learning_workspace import digest
from test_reference_upgrade import ws, app_client


def integration(ws, method="simpson", expression="exp(x)"):
    work,_=ws
    task=IntegrationTask(method=method,expression=expression,limit=8,tolerance=1e-8)
    run=run_numerical(task);run.update(id="integral",source_hash=digest(task.model_dump()))
    work.save("alice","numerical_lab","integral",run)
    return run,IntegrationContextRef(kind="integration_lab",record_id="integral",source_hash=run["source_hash"],schema_version="numerical-lab-v1",selected_step=0)


@pytest.mark.parametrize("method",["trapezoid","simpson","adaptive_simpson"])
def test_integral_snapshot_keeps_actual_estimates_and_cost(ws,method):
    run,ref=integration(ws,method)
    snap=resolve_learning_context(ws[0],"alice",ref)
    assert snap["task"]==run["task"] and snap["conditions"]==run["conditions"]
    assert snap["rows"][0]["work"]==run["rows"][0]["work"]
    assert snap["rows"][0]["value"]==run["rows"][0]["value"]
    assert snap["estimate_is_bound"] is False and snap["independent_success"] is False
    assert "residual" not in snap["rows"][0] and "error_bound" not in snap["rows"][0]
    assert ("intervals" in snap["rows"][0])==(method!="adaptive_simpson")
    with pytest.raises(KeyError):resolve_learning_context(ws[0],"bob",ref)


@pytest.mark.parametrize("corruption",["scope","value","cost","row","intervals","estimate","bound","parity","hash","step"])
def test_integral_rejects_mixed_or_changed_records(ws,corruption):
    run,ref=integration(ws);bad=deepcopy(run)
    if corruption=="scope":bad["evidence_scope"]="strict_error_bound"
    if corruption=="value":bad["rows"][0]["value"]="1.0"
    if corruption=="cost":bad["rows"][0]["work"]=-1
    if corruption=="row":bad["rows"][0]["k"]=1
    if corruption=="intervals":bad["rows"][0]["intervals"]=6
    if corruption=="estimate":bad["rows"][1]["error_estimate"]=-1
    if corruption=="bound":bad["rows"][0]["error_bound"]=0
    if corruption=="parity":bad["task"]["intervals"]=3
    if corruption=="hash":bad["source_hash"]="b"*64
    if corruption=="step":ref=ref.model_copy(update={"selected_step":100})
    ws[0].save("alice","numerical_lab","integral",bad)
    with pytest.raises(ValueError):resolve_learning_context(ws[0],"alice",ref)


def test_aliasing_keeps_zero_estimate_without_certifying_accuracy(ws):
    run,ref=integration(ws,"simpson","sin(16*pi*x)^2")
    snap=resolve_learning_context(ws[0],"alice",ref)
    assert run["rows"][-1]["error_estimate"]<1e-8
    assert abs(run["rows"][-1]["value"]-0.5)>0.4
    assert snap["estimate_is_bound"] is False
    assert any("振荡" in c for c in snap["conditions"])


def test_integral_chat_sse_reuses_reference_boundary(ws,monkeypatch):
    _,ref=integration(ws)
    client,_=app_client(ws,monkeypatch)
    response=client.post("/api/tutor/stream",json={"session_id":ws[0].repository.create_session("alice","数值分析")["session_id"],"user_id":"alice","message":"解释当前细分的估计与求值成本","learning_context":ref.model_dump()})
    assert response.status_code==200
    assert 'event: done' in response.text
    assert 'root_proposals' not in response.text
    assert ws[0].repository.list_mastery("alice")==[]

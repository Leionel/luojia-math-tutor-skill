from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes_tutor import router
from app.auth import Principal, get_principal
from app.main_deps import get_learning_workspace
from app.tutor.learning_actions import LearningActions, PreviewActionRequest, SavePreviewRequest, root_proposal
from app.tutor.learning_context import resolve_learning_context
from test_learning_workspace import workspace, practice, complete
from test_learning_context import saved, reference


def delivered(workspace, commit=True):
    run=saved(workspace);session=workspace.repository.create_session("alice","数值分析")["session_id"]
    run_id=str(uuid4());workspace.repository.start_agent_run(run_id,session,"alice","v","v")
    proposal=root_proposal(resolve_learning_context(workspace,"alice",reference(run)),run_id)
    message=workspace.repository.add_message(session,"assistant","讨论实验后可以预览参数。",
        learning_meta={"answer_guard":{"status":"passed"},"tutor_artifacts":[proposal]},
        agent_run_finish={"run_id":run_id,"user_id":"alice","status":"succeeded"} if commit else None)
    service=LearningActions(workspace,workspace.repository)
    return service,session,message,proposal


def preview_request(proposal, request_id="preview-one", initial=-2):
    return PreviewActionRequest(context=proposal["context"], parameters={**proposal["parameters"],"initial_value":initial},request_id=request_id)


def save_request(proposal, preview, observation="改初值后轨迹接近负根；仍需核对局部条件。"):
    return SavePreviewRequest(context=proposal["context"],preview_id=preview["id"],preview_hash=preview["input_hash"],observation=observation)


def test_only_delivered_owned_guarded_visible_messages_authorize_actions(workspace):
    service,s,m,p=delivered(workspace,False)
    with pytest.raises(KeyError):service.preview("alice",s,m,p["artifact_id"],preview_request(p))
    with workspace.repository.connect() as conn:
        workspace.repository._finish_agent_run(conn,p["run_id"],"alice","succeeded",message_id=m)
    assert service.state("alice",s,m,p["artifact_id"])["state"]=="proposed"
    with pytest.raises(KeyError):service.state("bob",s,m,p["artifact_id"])
    with pytest.raises(KeyError):service.state("alice","wrong",m,p["artifact_id"])
    with pytest.raises(KeyError):service.state("alice",s,m,str(uuid4()))
    workspace.repository.truncate_messages_after(s,m)
    with pytest.raises(KeyError):service.preview("alice",s,m,p["artifact_id"],preview_request(p))


def test_concurrent_preview_is_idempotent_exposes_help_without_formal_learning_records(workspace):
    service,s,m,p=delivered(workspace);req=preview_request(p)
    with ThreadPoolExecutor(4) as pool:
        previews=list(pool.map(lambda _:service.preview("alice",s,m,p["artifact_id"],req),range(4)))
    assert all(v==previews[0] for v in previews)
    assert previews[0]["rows"][1]["x"]==pytest.approx(-1.8)
    assert "提交轨迹" not in previews[0]["diagnosis"]["summary"]
    assert len(workspace.store.learning_records("alice",workspace.course_id,"lab_preview"))==1
    assert len(workspace.store.learning_records("alice",workspace.course_id,"lab"))==1
    assert workspace.repository.list_mastery("alice")==[]
    events=workspace.store.list_events("alice",workspace.course_id)
    assert len(events)==1 and events[0]["event_type"]=="hint_exposed" and events[0]["payload"]["help_level"]==3
    assert service.state("alice",s,m,p["artifact_id"])["used_help"]==3
    with pytest.raises(ValueError,match="标识"):
        service.preview("alice",s,m,p["artifact_id"],preview_request(p,initial=-1))


def test_preview_budget_newest_hash_and_save_retry(workspace):
    service,s,m,p=delivered(workspace);a=p["artifact_id"]
    previews=[service.preview("alice",s,m,a,preview_request(p,f"p-{i}",-2+i/10)) for i in range(3)]
    with pytest.raises(ValueError,match="三次"):service.preview("alice",s,m,a,preview_request(p,"fourth"))
    with pytest.raises(ValueError,match="最新"):service.save("alice",s,m,a,save_request(p,previews[0]))
    with pytest.raises(ValueError,match="预览"):
        service.save("alice",s,m,a,save_request(p,previews[-1]).model_copy(update={"preview_hash":"0"*64}))
    result=service.save("alice",s,m,a,save_request(p,previews[-1]))
    assert service.save("alice",s,m,a,save_request(p,previews[-1]))==result
    assert result["rows"]==previews[-1]["rows"] and result["prediction_timing"]=="after_preview"
    assert result["independent_success"] is False and len(workspace.store.learning_records("alice",workspace.course_id,"lab"))==2
    assert service.state("alice",s,m,a)["saved_run"]["id"]==result["id"]
    with pytest.raises(ValueError):service.save("alice",s,m,a,save_request(p,previews[-1],"不同观察"))
    with pytest.raises(ValueError,match="已经保存"):service.preview("alice",s,m,a,preview_request(p,"after-save"))


def test_actions_recheck_help_even_for_cached_preview_and_existing_save(workspace):
    service,s,m,p=delivered(workspace);a=p["artifact_id"]
    preview=service.preview("alice",s,m,a,preview_request(p))
    assessment=workspace.new_assessment("alice")
    for action in [lambda:service.state("alice",s,m,a),lambda:service.preview("alice",s,m,a,preview_request(p)),
                   lambda:service.save("alice",s,m,a,save_request(p,preview))]:
        with pytest.raises(ValueError,match="自检"):action()
    workspace.end_assessment("alice",assessment["id"])
    with pytest.raises(ValueError,match="不同"):
        service.preview("alice",s,m,a,preview_request(p).model_copy(update={"context":reference(saved(workspace,request_id="other"))}))
    assert len(workspace.store.learning_records("alice",workspace.course_id,"lab_preview"))==1


def test_expired_card_and_failed_message_never_execute(workspace):
    service,s,m,p=delivered(workspace);p["expires_at"]="2000-01-01T00:00:00+00:00"
    import json
    with workspace.repository.connect() as conn:
        conn.execute("update messages set learning_meta=? where id=?",(json.dumps({"answer_guard":{"status":"passed"},"tutor_artifacts":[p]}),m))
    assert service.state("alice",s,m,p["artifact_id"])["state"]=="expired"
    with pytest.raises(ValueError,match="过期"):service.preview("alice",s,m,p["artifact_id"],preview_request(p))
    with workspace.repository.connect() as conn:
        conn.execute("update agent_runs set status='failed' where id=?",(p["run_id"],))
    with pytest.raises(KeyError):service.state("alice",s,m,p["artifact_id"])
    assert not workspace.store.learning_records("alice",workspace.course_id,"lab_preview")


def test_unsaved_exposure_is_excluded_from_independent_probe_pool(workspace):
    task=practice(workspace);task=complete(workspace,task)
    workspace.course.overlay_store.record_process_event("unsaved-preview","alice",workspace.course_id,[],
        event_type="hint_exposed",help_level=3,metadata={"origin":"root_lab_preview","function":"(x*x)-3.0"})
    result=workspace.episodes.start_probe("alice",task["session_id"],task["episode_id"])
    assert result["challenge"]["function"] != "x^2-3"


def test_http_action_rejects_dynamic_tools_forged_parameters_and_owner(workspace):
    service,s,m,p=delivered(workspace);app=FastAPI();app.include_router(router)
    app.dependency_overrides[get_learning_workspace]=lambda:workspace
    app.dependency_overrides[get_principal]=lambda:Principal("alice",True)
    base=f"/api/tutor/sessions/{s}/messages/{m}/artifacts/{p['artifact_id']}"
    payload=preview_request(p).model_dump()
    with TestClient(app) as client:
        assert client.post(base+"/preview",json={**payload,"tool":"python"}).status_code==422
        assert client.post(base+"/preview",json={**payload,"parameters":{**payload["parameters"],"function":"x^2-3"}}).status_code==422
        assert client.post(base+"/preview",json={**payload,"parameters":{**payload["parameters"],"max_iterations":101}}).status_code==422
        assert client.post(base+"/preview",json=payload).status_code==200
        assert client.get(base).json()["state"]=="previewed"
        app.dependency_overrides[get_principal]=lambda:Principal("bob",True)
        assert client.post(base+"/preview",json=payload).status_code==404
        assert client.get(base).status_code==404

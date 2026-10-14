"""Offline browser acceptance server. Fixed replies are protocol fixtures, not gold.

Run from the repository root:
  python scripts/r3_ui_fixture.py --data-dir results/r3-ui-fixture --port 8101
It binds loopback, uses separate databases and never accesses a model provider.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

os.environ["LUOJIA_NO_DOTENV"] = "1"
for key in ("LLM_API_KEY", "MINERU_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_API_KEY"):
    os.environ.pop(key, None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api"))


def create_fixture(directory: Path):
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.config import Settings
    from app.auth import Principal, get_principal
    from app.main_deps import get_app_settings, get_learning_workspace, get_orchestrator, get_repository
    from app.knowledge.course_service import CourseService
    from app.knowledge.course_store import CourseStore
    from app.memory.repository import Repository
    from app.tutor.learning_workspace import LearningWorkspace
    from app.tutor.orchestrator import TutorOrchestrator
    from app.api import routes_sessions, routes_tutor, routes_learning, routes_models, routes_notes, routes_mastery
    from app.llm.openai_compatible import OpenAICompatibleClient
    directory.mkdir(parents=True, exist_ok=True)
    settings=Settings(database_url=f"sqlite:///{directory.resolve() / 'sessions.db'}",llm_api_key="",allow_user_api_key=False,typed_math_tools_enabled=False,teaching_decision_enabled=True)
    repository=Repository(settings)
    workspace=LearningWorkspace(CourseService(store=CourseStore(str(directory.resolve() / "course.db"))),repository)
    tutor=TutorOrchestrator(settings,repository)
    async def fixture_response(messages,*args,**kwargs):
        await asyncio.sleep(1.5)  # observable in-flight state for cancellation checks
        slot=next((json.loads(m["content"].split("[NODE_CONTEXT]\n",1)[1].split("\n[/NODE_CONTEXT]",1)[0]) for m in reversed(messages) if m.get("role")=="developer" and m["content"].startswith("[NODE_CONTEXT]")),{})
        inputs=slot.get("teaching_decision") or {}
        bundle=inputs.get("sources") or {};sources=bundle.get("sources",[])
        ids={item["id"] for item in sources};ref=bundle.get("context_ref") or {}
        decision={"claim_ref":"claim:current","evidence_refs":[],"known_conditions":[],"missing_conditions":["要讨论的一般结论及其适用条件"],"claim_status":"unknown","action":"explain" if inputs.get("disclosure")=="full" else "ask_missing_condition","disclosure":inputs.get("disclosure","scaffolded"),"reason":"实验轨迹描述这一次计算，一般性主张仍需核对条件。","assessments":[]}
        selections=[{"component":"ConditionChecklist","evidence_ref":"claim:current"}]
        if "context:rows" in ids:selections.append({"component":"RunTraceChart","evidence_ref":"context:rows"})
        if "context:parameters" in ids and not ref.get("activity_claim"):
            selections.extend([{"component":"ParameterCompare","evidence_ref":"context:parameters"},{"component":"PredictionForm","evidence_ref":"context:parameters"}])
        text="开发验收固定响应：本轮引用的轨迹仅描述保存的计算。局部现象与一般收敛结论需要分别核对；请说明你希望检验的条件。"
        return f"[TEACHING_DECISION]{json.dumps(decision,ensure_ascii=False)}[/TEACHING_DECISION][INTELLIGENT_UI]{json.dumps(selections,ensure_ascii=False)}[/INTELLIGENT_UI][OUTPUT]{text}"
    tutor.workflow_owner._collect_model_response=fixture_response
    # Title/note adapters also cannot escape to a provider.
    async def offline_stream(*args,**kwargs):
        yield "本地交互验收"
    async def offline_completion(*args,**kwargs):
        return "本地交互验收"
    OpenAICompatibleClient.stream=offline_stream
    OpenAICompatibleClient.chat_completion=offline_completion
    routes_learning.workspace=lambda:workspace
    app=FastAPI(title="R3 offline UI fixture")
    for module in (routes_sessions,routes_tutor,routes_learning,routes_models,routes_notes,routes_mastery):app.include_router(module.router)
    app.add_middleware(CORSMiddleware,allow_origins=["http://127.0.0.1:3100","http://localhost:3100"],allow_methods=["*"],allow_headers=["*"])
    def provider(value):
        return lambda:value
    for dependency,value in ((get_app_settings,settings),(get_repository,repository),(get_learning_workspace,workspace),(get_orchestrator,tutor),(get_principal,Principal("demo-user",True))):
        app.dependency_overrides[dependency]=provider(value)
    @app.get("/health")
    def health():return {"ok":True,"fixture":True,"model_calls":0}
    return app


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--data-dir",type=Path,required=True);parser.add_argument("--port",type=int,default=8101)
    args=parser.parse_args()
    import uvicorn
    uvicorn.run(create_fixture(args.data_dir),host="127.0.0.1",port=args.port)

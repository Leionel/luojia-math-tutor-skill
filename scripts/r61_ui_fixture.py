"""Offline R6.1 browser acceptance: isolated stores and visibly fixed model advice.

python scripts/r61_ui_fixture.py --data-dir results/r61/browser-data --port 8161
All mathematical executions use real local runners; model text is a fixture.
"""
import argparse
import json
from pathlib import Path
from r3_ui_fixture import create_fixture


def create_app(directory):
    from app.api import routes_explorations, routes_numerical_lab, routes_auth, routes_courses
    from app.main_deps import get_app_settings, get_learning_workspace
    from app.llm.openai_compatible import OpenAICompatibleClient
    from app.tutor.explorations import proposal
    from fastapi.middleware.cors import CORSMiddleware
    import httpx
    app=create_fixture(directory)
    settings=app.dependency_overrides[get_app_settings]()
    settings.llm_api_key="offline-fixture-only"
    workspace=app.dependency_overrides[get_learning_workspace]()
    for module in (routes_explorations,routes_numerical_lab,routes_auth,routes_courses):app.include_router(module.router)
    routes_numerical_lab.workspace=lambda:workspace
    routes_courses.get_course_service=lambda *args,**kwargs:workspace.course
    app.add_middleware(CORSMiddleware,allow_origins=["http://127.0.0.1:3161"],allow_methods=["*"],allow_headers=["*"])
    async def fixed_advice(self,messages,**kwargs):
        try:
            data=json.loads(messages[-1]["content"])
        except (ValueError,TypeError):
            return "离线探索讨论"
        if not isinstance(data,dict) or "context" not in data:
            return "离线探索讨论"
        claim=data["context"]["student_claim"]["text"]
        newton="newton" in claim.lower() or "牛顿" in claim
        tasks=[dict(domain="root_finding",method="newton",function="x^3-2*x+2",initial_value=x,tolerance=1e-6,limit=12) for x in (0,-2)] if newton else proposal()["tasks"]
        response={"decision":{"claim_ref":"claim:current","evidence_refs":["claim:current","context:personal_relations"],
                    "known_conditions":["离线夹具所指定的函数与参数"],"missing_conditions":["一般收敛结论的适用条件"],
                    "claim_status":"unknown","action":"offer_experiment","disclosure":"scaffolded",
                    "reason":"离线验收固定建议：比较初值与残差；此文案不能用作真实模型能力证据。", "assessments":[],
                    "experiment_proposal":{"changed_parameter":"task_parameters","question_to_test":"指定条件下的轨迹如何变化？", "observable":"有限轨迹、残差和相邻步变化", "tasks":tasks}},
                  "suggested_graph":{"nodes":[{"id":"condition","label":"初值与条件"},{"id":"convergence","label":"收敛判断"}],
                                     "edges":[{"id":"e","source":"condition","target":"convergence","relation":"related","reason":"离线候选：需要核对条件才能作收敛判断"}]},
                  "follow_up":"离线验收追问：哪项观察使你需要修订原判断？有限轨迹不能证明一般收敛。"}
        return json.dumps(response,ensure_ascii=False)
    OpenAICompatibleClient.chat_completion=fixed_advice
    def deny(*args,**kwargs):raise RuntimeError("R6.1 browser fixture prohibits external HTTP")
    async def deny_async(*args,**kwargs):deny()
    httpx.Client.send=deny;httpx.AsyncClient.send=deny_async
    @app.get("/_fixture/r61")
    def receipt():return {"fixture":True,"external_model_calls":0,"mathematics":"existing_local_runners"}
    return app


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--data-dir",type=Path,required=True);parser.add_argument("--port",type=int,default=8161)
    args=parser.parse_args()
    import uvicorn
    uvicorn.run(create_app(args.data_dir),host="127.0.0.1",port=args.port)

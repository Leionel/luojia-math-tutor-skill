"""Opt-in, three-case exploration capability capture using synthetic questions.

This entry does not contact any provider without --live --acknowledge-cost.
It records suggestions and executes their parameters locally, without quality scores.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"apps/api"))
CASES=[("gs","GS 不严格行对角占优就一定发散吗？我想检验必要条件与充分条件的区别。"),
       ("newton","Newton法求 f(x)=x^3-2*x+2，初值0出现0到1再回0；怎样比较另一个初值并修订全局收敛判断？"),
       ("missing","第三步比第二步小，能说明一定收敛吗？")]


async def run(output, settings=None, with_history=False):
    from app.config import get_settings
    from app.memory.repository import Repository
    from app.knowledge.course_store import CourseStore
    from app.knowledge.course_service import CourseService
    from app.tutor.learning_workspace import LearningWorkspace
    from app.tutor.explorations import Explorations, Create, Execute, EditGraph, PersonalGraph, Revise
    from app.tutor.exploration_advice import advise, AdviceRequest
    from app.llm.openai_compatible import OpenAICompatibleClient
    import app.tutor.exploration_advice as advice_module
    from app.llm.call_observation import observation
    settings=settings or get_settings()
    if not settings.llm_api_key:raise SystemExit("No server model key configured; no request sent.")
    raw_responses=[]
    class BudgetClient(OpenAICompatibleClient):
        calls=0
        def build_request_payload(self,*args,**kwargs):
            payload=super().build_request_payload(*args,**kwargs)
            field="max_completion_tokens" if "max_completion_tokens" in payload else "max_tokens"
            payload[field]=min(payload.get(field,1536),1536)
            return payload
        async def chat_completion(self,*args,**kwargs):
            if BudgetClient.calls>=3:raise RuntimeError("three-call budget exhausted")
            BudgetClient.calls+=1
            raw=await super().chat_completion(*args,**kwargs)
            raw_responses.append(raw)
            return raw
    report={"scope":"unscored_real_model_capture", "max_model_calls":3,"requested_output_tokens_per_call":1536,
            "billing_boundary":"provider request parameter, not a verified monetary cap",
            "actual_cost":None,"human_review":"pending","cases":[]}
    output.parent.mkdir(parents=True,exist_ok=True)
    with patch.object(advice_module,"OpenAICompatibleClient",BudgetClient), TemporaryDirectory(prefix="r61-eval-") as directory:
        isolated=settings.model_copy(update={"database_url":f"sqlite:///{Path(directory)/'sessions.db'}"})
        repo=Repository(isolated);repo.ensure_user("r61-synthetic")
        workspace=LearningWorkspace(CourseService(store=CourseStore(str(Path(directory)/"course.db"))),repo)
        try:
            for id,claim in CASES:
                service=Explorations(workspace)
                current=service.create("r61-synthetic",Create(request_id=id,title=id,claim=claim))
                if with_history and id=="newton":
                    current=service.update("r61-synthetic",id,"graph",EditGraph(request_id="synthetic-graph",expected_revision=current["revision"],graph=PersonalGraph(
                        nodes=[{"id":"initial","label":"任意初值"},{"id":"converge","label":"Newton收敛"}],
                        edges=[{"id":"hypothesis","source":"initial","target":"converge","relation":"implies","reason":"我曾把局部收敛条件推广到了任意初值"}]
                    )))
                    current=service.update("r61-synthetic",id,"run",Execute(request_id="synthetic-prior-run",expected_revision=current["revision"],
                        tasks=[{"domain":"root_finding","method":"newton","function":"x^3-2*x+2","initial_value":x,"limit":10} for x in (0,-2)],
                        prediction="初值可能改变轨迹",metrics=["residual","step"],confirmed=True))
                    current=service.update("r61-synthetic",id,"revise",Revise(request_id="synthetic-revision",expected_revision=current["revision"],
                        claim="初值0在0和1间循环，负初值这次收敛；原来任意初值都收敛的关系需要修订。接下来如何解释局部收敛条件？",reason="依据已保存的两组真实数值轨迹"))
                events=[]
                async def sink(phase,status,**fields):events.append({"phase":phase,"status":status,**fields})
                before=len(raw_responses)
                with observation(sink,f"r61-{id}"):
                    result=await advise(workspace,"r61-synthetic",id,AdviceRequest(expected_revision=current["revision"]),settings)
                saved=result.pop("exploration",None)
                row={"id":id,"claim":current["claim"],"history_seeded":with_history and id=="newton","advice":result,"local_execution":None,"model_receipts":events,"raw_response":raw_responses[-1] if len(raw_responses)>before else None}
                proposed=(result.get("decision") or {}).get("experiment_proposal")
                if proposed and saved:
                    executed=service.update("r61-synthetic",id,"run",Execute(request_id=f"{id}-run",expected_revision=saved["revision"],tasks=proposed["tasks"],prediction="脚本检验参数可执行性，不代表学生预测",metrics=["residual","step"],confirmed=True))
                    row["local_execution"]=executed["history"][-1]["payload"]
                report["cases"].append(row)
                output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        finally:
            workspace.store.close()
    print(output)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--live",action="store_true");parser.add_argument("--acknowledge-cost",action="store_true");parser.add_argument("--with-history",action="store_true");parser.add_argument("--output",type=Path,default=ROOT/"results/r61/real-model.json")
    args=parser.parse_args()
    if not (args.live and args.acknowledge_cost):
        print(json.dumps({"status":"not_run","questions":CASES,"required":"explicit cost authorization plus --live --acknowledge-cost"},ensure_ascii=False,indent=2))
    else:asyncio.run(run(args.output,with_history=args.with_history))

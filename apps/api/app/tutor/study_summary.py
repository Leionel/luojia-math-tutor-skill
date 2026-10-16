"""Read existing plans only; task navigation does not generate help or grades."""
import json,re,asyncio,hashlib
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from app.tutor.help_boundary import assert_reference_help_allowed
from app.math_tools.verifier import VerifyResult
from app.tutor.run_trace import RunTrace,durable_call


def study_requested(message):
    return message.strip().rstrip('？?。！!').strip() in {'今天学什么','今天的任务','查看当前任务','查看学习计划','继续上次任务','继续学习的任务'}


def read_study_summary(workspace,owner):
    date=datetime.now(ZoneInfo('Asia/Hong_Kong')).date().isoformat()
    with workspace.store.transaction():
        locked=False
        try:assert_reference_help_allowed(owner,workspace.course)
        except ValueError:locked=True
        plan=workspace.store.learning_record(owner,workspace.course_id,'plan',date)
        revision=workspace.revision();tasks=[]
        closed={'read_complete','assisted_complete','verified_complete'}
        pending=[t for t in workspace.store.learning_records(owner,workspace.course_id,'task') if t.get('state') not in closed]
        if plan or pending:
            ids=plan.get('task_ids',[]) if plan else [t['id'] for t in reversed(pending)]
            if not isinstance(ids,list):raise ValueError('计划记录不可读取')
            for id in ids[:3]:
                if not isinstance(id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',id):raise ValueError('任务标识不可读取')
                task=workspace.store.learning_record(owner,workspace.course_id,'task',id)
                state=task.get('state','unknown') if task else 'missing'
                stale=not task or task.get('graph_revision')!=revision
                session=task.get('session_id') if task else None
                session_valid=not session or workspace.repository.session_belongs_to(session,owner)
                if not session_valid:state='session_unavailable'
                tasks.append({'id':id,'title':'当前任务（请回工作区作答）' if locked else str(task.get('title','任务已不可用') if task else '任务已不可用')[:120],
                              'state':state,'stale':stale,'session_available':session_valid,'kind':task.get('kind','unknown') if task else 'unknown'})
        recommendation = {'policy_version':'r1-b1-v1','graph_revision':revision,
            'evidence_kind':'saved_state_only','mastery_claim':False,'kind':'assessment_in_progress' if locked else 'choose_task',
            'title':'继续当前自检' if locked else '核对今日学习记录',
            'reason':'自检期间只显示回到作答的入口。' if locked else '记录不完整时请回工作区核对，不推断掌握度。',
            'href':'/assessment' if locked else '/study','source_id':None}
        if not locked:
            try:
                recommendation=workspace.overview(owner)['recommendation']
            except (KeyError, ValueError, TypeError):
                # Old or partially missing task records remain visible above; do not invent a direct link.
                pass
        return {'version':'study-summary-v1','local_date':date,'read_at':datetime.now(timezone.utc).isoformat(),
            'plan_exists':bool(plan),'stale':bool(plan and plan.get('graph_revision')!=revision),'help_locked':locked,
            'tasks':tasks,'omitted_tasks':max(0,len(ids)-3) if plan or pending else 0,
            'recommendation':recommendation,'read_only':True,'independent_success':False}


def event(name,data):return 'event: '+name+'\ndata: '+json.dumps(data,ensure_ascii=False)+'\n\n'


async def stream_study_summary(repo,workspace,owner,session,message):
    trace=RunTrace(repo,session,owner)
    try:
        yield event('opening',{'content':'我先读取你已保存的学习任务。\n\n'})
        await trace.start();await trace.step('context','started')
        summary=await asyncio.to_thread(read_study_summary,workspace,owner)
        await trace.step('context','succeeded')
        content='今天没有计划，下面可续接此前未完成任务。读取不会创建计划。' if not summary['plan_exists'] and summary['tasks'] else '当前没有今天的计划，可以到今日学习安排。读取任务不会自动创建计划。' if not summary['plan_exists'] else '下面是本轮读取的任务状态。请回原工作区继续；打开卡片不会把任务标成完成。'
        if summary['help_locked']:content+=' 当前仅显示任务入口，请先完成待答检验或自检。'
        meta={'intent':'study_resume','verified':False,'is_correct':None,'verification_kind':'none','concepts':[],
              'step_check':VerifyResult(False,None,'仅读取任务，不核对作答。',input_hash=hashlib.sha256(message.encode()).hexdigest()).public(),'verifier_summary':'仅读取任务，不核对作答。','study_summary':summary,'agent_run':trace.terminal_snapshot('succeeded')}
        yield event('meta',meta);yield event('token',{'content':content})
        await durable_call(repo.add_message,session,'user',message)
        id=await durable_call(repo.add_message,session,'assistant',content,learning_meta=meta,agent_run_finish=trace.finish_args('succeeded'))
        trace.committed('succeeded');meta['agent_run']=trace.snapshot(message_id=id)
        yield event('run_event',meta['agent_run']);yield event('meta_update',meta)
        yield event('done',{'message_id':id,'metrics':{'llm_call_count':0,'route':'study_read'}})
    except Exception:
        if trace.started and trace.status=='running':await trace.finish('failed')
        yield event('error',{'code':'study_read_failed','message':'任务读取失败，未修改计划；可以重试。'})
    finally:
        if trace.started and trace.status=='running':await trace.finish('interrupted')

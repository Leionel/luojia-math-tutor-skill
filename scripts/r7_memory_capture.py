"""Persisted public development recall probes and reproducible selection workload."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from statistics import median
from unittest.mock import patch
from r5_quality import ROOT, sha
from r7_quality import write
from r64_capture import isolate


def dataset(directory, count):
    from app.config import Settings
    from app.knowledge.course_store import CourseStore
    from app.knowledge.course_service import CourseService
    from app.memory.repository import Repository
    from app.tutor.learning_workspace import LearningWorkspace, digest
    from app.tutor.explorations import Explorations, Create, EditGraph, PersonalGraph
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory/'synthetic.json'
    w = LearningWorkspace(CourseService(store=CourseStore(directory/'course.db')),
                         Repository(Settings(database_url='sqlite:///'+str(directory/'sessions.db'))))
    owner = 'r7-memory-synthetic'
    if marker.exists():
        if json.loads(marker.read_text()) != dict(owner=owner, count=count):
            raise ValueError('different dataset; choose a fresh directory')
        return w, owner
    if w.store.learning_records(owner, w.course_id, 'exploration'):
        raise ValueError('unmarked existing data refused')
    w.repository.ensure_user(owner)
    session = w.repository.create_session(owner, '数值分析')['session_id']
    note = w.repository.save_note(owner, session, '合成条件', '合成私人笔记；不是课程定理')
    graph = dict(nodes=[dict(id='initial', label='初值', source_ref=dict(kind='note', note_id=note,
                      source_hash=digest('合成私人笔记；不是课程定理'))), dict(id='conclusion', label='Newton收敛')],
                 edges=[dict(id='edge', source='initial', target='conclusion', relation='implies',
                             reason='旧猜测：任意初值都收敛；尚未经数学审核')])
    service = Explorations(w)
    for i in range(count):
        id = f'old-{i:02}'
        service.create(owner, Create(request_id=id, title='旧Newton判断', claim='Newton任意初值都收敛'))
        service.update(owner, id, 'graph', EditGraph(request_id='graph', expected_revision=1,
                                                    graph=PersonalGraph.model_validate(graph)))
    marker.write_text(json.dumps(dict(owner=owner, count=count)), encoding='utf-8')
    return w, owner


def probes(w, owner):
    from app.tutor.personal_recall import select_personal_context
    cases = [
        ('literal', 'Newton 换初值有什么影响？', True, 'same method and initial-value concept'),
        ('synonym-cn', '牛顿法换个出发点会怎样？', True, '出发点 means initial value in this explicit Newton question'),
        ('same-method-other-concept', 'Newton 导数为零时为什么不能更新？', False,
         'division by zero is not the stored initial-value convergence inference'),
        ('other-domain', 'Simpson 积分误差估计能当界吗？', False, 'different method and concept'),
    ]
    rows = []
    for id, question, expected, basis in cases:
        selected = select_personal_context(w, owner, question)
        rows.append(dict(id=id, question=question, expected=expected, selected=selected,
                         matched=bool(selected)==expected, basis=basis, source='agent_prepared_development_label'))
    return rows


def performance(w, owner):
    from app.tutor.personal_recall import select_personal_context
    from app.tutor.explorations import Explorations
    original = Explorations.bind; counts = []; times = []; contexts = []
    for _ in range(7):
        calls = []
        def bind(self, *args, **kwargs):
            calls.append(1); return original(self, *args, **kwargs)
        with patch.object(Explorations, 'bind', bind):
            start = time.perf_counter(); selected = select_personal_context(w, owner, 'Newton 初值如何影响收敛？')
            times.append(round((time.perf_counter()-start)*1000, 3)); counts.append(len(calls)); contexts.append(sha(selected))
    return dict(samples=7, duration_ms=times, median_ms=median(times), bind_calls=counts,
                selected_sha256=contexts, input_scope='same persisted synthetic 30-record dataset, same query, limit=2',
                model_requests=0, token_usage=None, model_quality=None)


def feedback(w, owner):
    from copy import deepcopy
    from app.tutor.personal_recall import select_personal_context, validate_personal_context
    from app.tutor.explorations import Explorations, Revise, EditGraph, PersonalGraph, SaveAdvice, RelationDecision
    question='牛顿法换个出发点会怎样？'; service=Explorations(w)
    before=select_personal_context(w, owner, question)
    official=sha(w.store.load_graph(w.course_id)); value=service.get(owner,'old-00')
    value=service.update(owner,'old-00','revise',Revise(request_id='correction',expected_revision=value['revision'],
        claim='Newton不是任意初值都收敛',reason='学生撤回原全称猜测；仍保留原话'))
    graph=deepcopy(value['graph']);graph['edges'][0].update(relation='challenges',reason='学生修订：初值会影响轨迹，不能作全称保证')
    value=service.update(owner,'old-00','graph',EditGraph(request_id='correct-edge',expected_revision=value['revision'],graph=PersonalGraph.model_validate(graph)))
    after=select_personal_context(w,owner,question)
    try: validate_personal_context(w,owner,before); old_selection_rejected=False
    except ValueError: old_selection_rejected=True
    # A separate model candidate must not be recalled while pending or rejected.
    from app.tutor.explorations import Create
    service.create(owner,Create(request_id='pending',title='模型意见',claim='Newton任意初值都收敛'))
    candidate=service.update(owner,'pending','advice',SaveAdvice(request_id='proposal',expected_revision=1,
        advice={'suggested_graph':graph}))['relation_candidates'][0]
    pending=select_personal_context(w,owner,question)
    service.update(owner,'pending','relation_decision',RelationDecision(request_id='reject',expected_revision=2,
        candidate_id=candidate['id'],candidate_version=1,decision='reject',reason='不接受模型的关系'))
    rejected=select_personal_context(w,owner,question)
    # Change original note bytes: old exact source must not be replaced.
    note=after[0]['evidence_refs'][0]['ref']['note_id']
    with w.repository.connect() as conn:conn.execute('update notes set content=? where id=?',('已更新，旧引用失效',note))
    stale=select_personal_context(w,owner,question)
    return dict(before=before,after=after,old_selection_rejected=old_selection_rejected,
        pending_ids=[r['exploration_id'] for r in pending],rejected_ids=[r['exploration_id'] for r in rejected],
        stale=stale,other_owner=select_personal_context(w,'other-owner',question),
        official_graph_unchanged=official==sha(w.store.load_graph(w.course_id)),
        mastery=w.repository.list_mastery(owner), independent_math_reviewed=False, model_quality=None)


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--data-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--performance', action='store_true')
    p.add_argument('--feedback', action='store_true')
    a = p.parse_args(); target=a.output.resolve(); directory=a.data_dir.resolve()
    if not target.is_relative_to(ROOT/'results') or not directory.is_relative_to(ROOT/'results') or target.exists():
        p.error('fresh output and synthetic directory inside results/ required')
    isolate(); target.parent.mkdir(parents=True, exist_ok=True)
    w, owner = dataset(directory, 30 if a.performance else 1)
    try:
        data = feedback(w,owner) if a.feedback else performance(w, owner) if a.performance else dict(cases=probes(w, owner), independent_math_reviewed=False,
            model_quality=None, comparison='selection plumbing only; no human or real-model effect')
        data['source_sha256'] = hashlib.sha256((ROOT/'apps/api/app/tutor/personal_recall.py').read_bytes()).hexdigest()
        write(target, data)
        print(json.dumps(data if a.performance else {'old_selection_rejected':data['old_selection_rejected'],
            'stale_count':len(data['stale']), 'official_graph_unchanged':data['official_graph_unchanged']} if a.feedback else
            [{'id':r['id'],'selected':len(r['selected']),'matched':r['matched']} for r in data['cases']]))
    finally: w.store.close()


if __name__=='__main__': main()

"""F1–F4 learning workspace. Curated development content is not research gold."""
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.knowledge.review_schedule import advance_review, POLICY_VERSION
from app.math_tools.root_runner import run_reference
from app.tutor.root_diagnostics import RootEpisodeService, RootSubmission
from app.tutor.help_boundary import assert_reference_help_allowed
from app.math_tools.root_finding import RootAttempt

CONTENT_VERSION = "root-learning-dev-v1"
ASSESSMENT_VERSION = "root-chapter-diagnostic-v1"
CARDS = {
    "NA_ROOT_FINDING": {"conditions": ["残差 |f(x)| 和根误差 |x-x*| 是不同的量", "若区间内有根且 |f'|≥m>0，可由中值定理给出 |x-x*|≤|f(x)|/m", "停止阈值必须说明目标是残差还是根误差"], "question": "把函数乘以很小的常数，会不会自动降低根误差？", "options": ["会", "不会，根的位置并不改变"], "answer": 1, "explanation": "缩放会降低残差，但不改变零点；需要相应的导数下界才能换算根误差。"},
    "NA_BISECTION": {"conditions": ["f 在闭区间连续", "两端严格变号；端点为根须单独处理", "半区间宽度可作为中点误差上界"], "question": "只有两端变号，能否直接确认中间有根？", "options": ["能", "还需要区间连续性"], "answer": 1, "explanation": "例如 1/x 在 [-1,1] 两端变号，但在 0 处不连续。"},
    "NA_NEWTON": {"conditions": ["迭代点处导数存在且非零", "单根且满足局部光滑性条件", "局部二阶收敛要求初值足够接近根"], "question": "单根的牛顿法是否对所有初值都二阶收敛？", "options": ["是", "不是，结论是局部的"], "answer": 1, "explanation": "局部收敛定理不保证远处初值收敛；可能出现循环或导数为零。"},
    "NA_FIXED_POINT": {"conditions": ["phi 将闭区间映回自身", "区间上有一致压缩常数 q<1", "初值位于该区间"], "question": "只在某一个点有 |phi'(x)|<1，够不够应用区间压缩定理？", "options": ["够", "不够，需要区间条件"], "answer": 1, "explanation": "需要区间不变性和整个区间上的一致压缩界。"},
}
# A separate development self-check pool; these keys never leave the server before submission.
QUESTIONS = [
    ("continuity", "二分法用变号确认区间存在根，还需要什么？", ["区间连续", "函数可任意间断", "初值足够大"], 0, "介值定理需要区间连续。", "NA_BISECTION"),
    ("width", "二分法当前区间 [1,1.125] 的中点误差上界是多少？", ["0.125", "0.0625", "无法给界"], 1, "中点到区间任意点至多为半宽 0.0625。", "NA_BISECTION"),
    ("update", "f(x)=x²−5，x₀=2，一次标准牛顿更新是？", ["2.25", "2.5", "1.75"], 0, "2−(4−5)/4=2.25。", "NA_NEWTON"),
    ("local", "单根牛顿法的二阶收敛结论通常是？", ["任意初值均成立", "满足条件时的局部结论", "与初值无关"], 1, "单根、光滑性、非退化性和初值邻域共同限制适用范围。", "NA_NEWTON"),
    ("residual", "残差很小是否自动意味着根误差很小？", ["总是", "还需要误差界条件", "残差就是根误差"], 1, "需要导数下界等条件才能由残差推出根误差上界。", "NA_ROOT_FINDING"),
    ("contraction", "压缩映射求根的区间条件包括？", ["只需一个点导数小于1", "区间不变且一致压缩", "只需最后两次迭代相近"], 1, "区间不变性和一致压缩缺一不可。", "NA_FIXED_POINT"),
]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


class LearningWorkspace:
    def __init__(self, course, repository):
        self.course, self.store, self.repository = course, course.store, repository
        self.course_id = course.course_id
        self.episodes = RootEpisodeService(course)

    def get(self, owner, kind, record_id):
        result = self.store.learning_record(owner, self.course_id, kind, record_id)
        if result is None:
            raise KeyError(record_id)
        return result

    def save(self, owner, kind, record_id, data):
        self.store.save_learning_record(owner, self.course_id, kind, record_id, data)
        return data

    def revision(self):
        graph = self.store.load_graph(self.course_id) or {}
        return self.store.latest_revision_id(self.course_id) or f"seed:{graph.get('seed_checksum', '')}"

    def today(self, owner, tz="Asia/Hong_Kong"):
        try:
            date = datetime.now(ZoneInfo(tz)).date().isoformat()
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("不支持的时区")
        plan = self.store.learning_record(owner, self.course_id, "plan", date)
        if plan:
            plan["tasks"] = [self.get(owner, "task", item) for item in plan["task_ids"]]
            plan["stale"] = plan["graph_revision"] != self.revision()
        return {"plan": plan, "local_date": date, "timezone": tz, "persistent": self.store.persistent,
                "reviews": self.store.learning_records(owner, self.course_id, "review")}

    def overview(self, owner, tz="Asia/Hong_Kong"):
        """Read-only summary. Progress categories are not mastery estimates."""
        with self.store.transaction():
            today = self.today(owner, tz)
            tasks = self.store.learning_records(owner, self.course_id, "task")
            revision = self.revision()
            closed = {"read_complete", "assisted_complete", "verified_complete"}
            pending = [t for t in tasks if t["state"] not in closed]
            valid = [t for t in pending if t["graph_revision"] == revision]
            priority = {"awaiting_check": 0, "needs_revision": 2, "unknown": 3, "in_progress": 4, "planned": 5}
            valid.sort(key=lambda t: 1 if t["kind"] == "review" and t["state"] == "in_progress" else priority.get(t["state"], 6))
            summary = lambda t: {k: t[k] for k in ("id", "title", "kind", "state", "unit_id", "reason")}
            assessments = self.store.learning_records(owner, self.course_id, "assessment")
            active = next((a for a in reversed(assessments) if a["state"] == "in_progress"), None)
            latest = next((a for a in reversed(assessments) if a["state"] == "completed"), None)
            public = self.assessment_public(latest) if latest else None
            now = datetime.now(timezone.utc)
            plan_tasks = today["plan"]["tasks"] if today["plan"] else []
            safe_tasks = [t for t in valid if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", t.get("id", ""))
                          and (not t.get("session_id") or self.repository.session_belongs_to(t["session_id"], owner))]
            due = sorted((r for r in today["reviews"] if datetime.fromisoformat(r["due_at"]) <= now),
                         key=lambda r: (r["due_at"], r["id"]))
            waiting = next((t for t in safe_tasks if t["state"] == "awaiting_check"), None)
            revision_task = next((t for t in safe_tasks if t["state"] == "needs_revision"), None)
            stale = sorted((t for t in pending if t.get("graph_revision") != revision),
                           key=lambda t: t.get("id", ""))
            recommendation = {"policy_version": "r1-b1-v1", "graph_revision": revision,
                              "evidence_kind": "saved_state_only", "mastery_claim": False}
            if active:
                recommendation.update(kind="assessment_in_progress", title="继续当前章节自检",
                                      reason="自检尚未交卷；先完成或主动结束，不把中途作答当成绩。",
                                      href="/assessment", source_id=active["id"])
            elif waiting or revision_task:
                selected = waiting or revision_task
                recommendation.update(kind="confirm_feedback" if waiting else "revise_process",
                    title="先确认这次过程反馈" if waiting else "修订上次求根过程",
                    reason="已保存反馈等待确认，确认后才能继续。" if waiting else "已保存任务标为需要修订；先回看原过程与反馈。",
                    href=f"/study?task={selected['id']}", source_id=selected["id"])
            elif due:
                recommendation.update(kind="due_review", title="安排到期复习",
                    reason="已有到期复习记录；先在今日学习核对能否开始新题，不据此推断已经遗忘。",
                    href="/study", source_id=due[0]["id"])
            elif stale:
                unit_id = stale[0].get("unit_id")
                current_units = {unit["id"] for unit in self.reading_units()}
                recommendation.update(kind="stale_source", title="核对已变化的课程来源",
                    reason="旧任务绑定的课程版本已变化；先阅读当前材料，不能直接沿用旧任务结果。",
                    href=f"/reading?unit={unit_id}" if unit_id in current_units else "/study",
                    source_id=stale[0].get("id"))
            elif safe_tasks:
                selected = safe_tasks[0]
                recommendation.update(kind="resume_task", title="继续已保存任务",
                    reason="这项任务尚未完成；打开只续接原记录，不自动给分。",
                    href=f"/study?task={selected['id']}", source_id=selected["id"])
            else:
                recommendation.update(kind="choose_task", title="选择今天的一项学习任务",
                    reason="目前没有可确认的待办状态；可以在今日学习自行选择，不猜测掌握度。",
                    href="/study", source_id=None)
            return {
                "local_date": today["local_date"], "persistent": today["persistent"],
                "plan": {"minutes": today["plan"]["minutes"], "total": len(plan_tasks),
                         "completed": sum(t["state"] in closed for t in plan_tasks), "stale": today["plan"]["stale"]} if today["plan"] else None,
                "next_task": summary(valid[0]) if valid else None,
                "recommendation": recommendation,
                "pending_tasks": [summary(t) for t in valid],
                "stale_tasks": len(pending) - len(valid),
                "due_reviews": sum(datetime.fromisoformat(r["due_at"]) <= now for r in today["reviews"]),
                "counts": {"reading": sum(t["state"] == "read_complete" for t in tasks),
                           "practice": sum(t["state"] == "assisted_complete" for t in tasks),
                           "independent": sum(t["state"] == "verified_complete" for t in tasks),
                           "notes": len(self.store.learning_records(owner, self.course_id, "reading_note")),
                           "labs": len(self.store.learning_records(owner, self.course_id, "lab")) + len(self.store.learning_records(owner, self.course_id, "numerical_lab")),
                           "teach_backs": len(self.store.learning_records(owner, self.course_id, "teach_back")),
                           "code_submissions": len(self.store.learning_records(owner, self.course_id, "code_submission"))},
                "active_assessment": {"id": active["id"], "answered": len(active["answers"]), "total": len(active["questions"])} if active else None,
                "latest_assessment": {"id": public["id"], "score": public["score"], "review_units": public["review_units"]} if public else None,
            }

    def plan(self, owner, minutes, tz):
        with self.store.transaction():
            today = self.today(owner, tz)
            if today["plan"]:
                return today
            date = today["local_date"]
            now = datetime.now(timezone.utc)
            due = sorted([r for r in today["reviews"] if datetime.fromisoformat(r["due_at"]) <= now], key=lambda r: r["due_at"])
            prior = self.store.learning_records(owner, self.course_id, "task")
            revision = next((t for t in reversed(prior) if t["state"] == "needs_revision"), None)
            assessments = self.store.learning_records(owner, self.course_id, "assessment")
            latest = next((a for a in reversed(assessments) if a["state"] == "completed"), None)
            weak_units = list(dict.fromkeys(q[5] for q in latest["questions"] if latest["answers"].get(q[0]) != q[3])) if latest else []
            if due:
                episode = self.episodes.owned(due[0]["parent_episode_id"], owner, due[0]["session_id"])
                can_probe = any(a["acknowledged"] and a["report"]["complete"] for a in episode["attempts"])
                selected = [("review", "到期复习：新的求根检验", "到达计划复习时间，并不意味着已经遗忘", due[0]["parent_episode_id"], due[0]["session_id"])] if can_probe else [("practice", "到期修订：先完成求根过程", "此前过程未完成，先修订再发独立新题", due[0]["parent_episode_id"], due[0]["session_id"])]
            elif revision:
                selected = [("practice", "修订求根过程", "上一次诊断发现过程偏差", revision.get("episode_id"), revision.get("session_id"))]
            else:
                selected = [("reading", "重温牛顿法适用条件", "先确认局部收敛与停止条件", None, None),
                            ("practice", "提交自己的牛顿迭代", "以受控轨迹核对更新与停止依据", None, None)]
                if weak_units:
                    selected[0] = ("reading", "复习章节诊断中待核对的条件", "最近一次参考题显示需要回看条件；不代表总体掌握度", None, None)
            if minutes == 30:
                selected.append(("reading", "比较二分法的保证", "对照变号、连续性与区间误差界", None, None))
            ids = []
            for kind, title, reason, episode_id, session_id in selected[:3]:
                task_id = uuid.uuid4().hex
                task = {"id": task_id, "kind": kind, "title": title, "reason": reason,
                        "state": "planned", "unit_id": weak_units[0] if "诊断" in title else "NA_BISECTION" if "二分" in title else "NA_NEWTON",
                        "graph_revision": self.revision(), "content_version": CONTENT_VERSION,
                        "study_session_id": f"study:{date}",
                        "parent_episode_id": episode_id if kind == "review" else None,
                        "episode_id": episode_id if kind == "practice" else None, "session_id": session_id}
                self.save(owner, "task", task_id, task)
                ids.append(task_id)
            self.save(owner, "plan", date, {"id": date, "minutes": minutes, "timezone": tz,
                      "task_ids": ids, "graph_revision": self.revision(), "policy_version": POLICY_VERSION})
            return self.today(owner, tz)

    def start(self, owner, task_id):
        with self.store.transaction():
            task = self.get(owner, "task", task_id)
            if task["graph_revision"] != self.revision():
                raise ValueError("课程版本已更新，请重新核对任务来源；旧任务不会被静默替换。")
            if task["kind"] != "reading" and not task.get("session_id"):
                # Repository and CourseStore have separate databases. A retry may
                # leave an unused session; it cannot create false learning evidence.
                task["session_id"] = self.repository.create_session(owner, self.course_id, "今日求根任务")["session_id"]
            if task["kind"] == "review" and not task.get("episode_id"):
                # Probe ownership is bound to its original practice session.
                probe = self.episodes.start_probe(owner, task["session_id"], task["parent_episode_id"])
                task.update(episode_id=probe["episode_id"], challenge=probe["challenge"])
            if task["kind"] == "practice" and "challenge" not in task:
                if task.get("episode_id"):
                    task["challenge"] = self.episodes.owned(task["episode_id"], owner, task["session_id"])["attempts"][0]["input"]
                else:
                    task["challenge"] = {"method": "newton", "function": "x^2-2", "initial_value": 1.0,
                                         "interval": [1.0, 2.0], "tolerance": 0.0001, "goal": "root_error"}
            if task["state"] == "planned":
                task["state"] = "in_progress"
            return self.save(owner, "task", task_id, task)

    def submit(self, owner, task_id, attempt, request_id):
        with self.store.transaction():
            task = self.get(owner, "task", task_id)
            if task["kind"] == "reading" or not task.get("session_id"):
                raise ValueError("请先开始求根任务")
            if task["graph_revision"] != self.revision():
                raise ValueError("任务来源版本已更新，请先核对材料")
            if task["state"] == "awaiting_check" and request_id != task["feedback"]["attempt_id"]:
                raise ValueError("请先确认当前反馈，再提交修订")
            if task["state"] in ("assisted_complete", "verified_complete") and request_id != task["feedback"]["attempt_id"]:
                raise ValueError("已完成的任务保留原结果，请换新题继续练习")
            expected = RootAttempt.model_validate(task["challenge"]).model_dump(exclude={"iterates", "brackets", "stop_reason"})
            actual = attempt.model_dump(exclude={"iterates", "brackets", "stop_reason"})
            if expected != actual:
                raise ValueError("提交必须保留服务端指定的题目、初值和目标")
            if len(attempt.iterates) < 2 or attempt.iterates[0] != task["challenge"]["initial_value"]:
                raise ValueError("请提交从指定初值开始的至少两个迭代值")
            result = self.episodes.submit(owner, task["session_id"], RootSubmission(attempt=attempt, attempt_id=request_id, episode_id=task.get("episode_id")), mode="practice")
            task.update(episode_id=result["episode_id"], feedback=result)
            if result["delivery"] != "acknowledged":
                task["state"] = "awaiting_check"
            self.save(owner, "task", task_id, task)
            return task

    def acknowledge(self, owner, task_id, attempt_id, feedback_id):
        with self.store.transaction():
            task = self.get(owner, "task", task_id)
            if not task.get("feedback") or task["feedback"]["feedback_id"] != feedback_id:
                raise ValueError("请确认当前显示的反馈，旧反馈不能覆盖新尝试")
            result = self.episodes.acknowledge(owner, task["session_id"], task["episode_id"], attempt_id, feedback_id)
            outcome = result["outcome"]
            task["feedback"].update(outcome=outcome, delivery="acknowledged")
            task.update(state={"independent_probe_success": "verified_complete", "assisted_success": "assisted_complete", "observed_success": "assisted_complete", "failed": "needs_revision"}.get(outcome, "unknown"))
            if outcome != "unknown":
                old = self.store.learning_record(owner, self.course_id, "review", task["unit_id"])
                # Only probe success advances a stage. Ordinary practice stays assisted.
                review = advance_review(old, outcome, feedback_id, task.get("study_session_id", f"legacy:{task['session_id']}"), datetime.now(timezone.utc))
                parent = task["episode_id"] if outcome in ("independent_probe_success", "assisted_success", "observed_success") else task.get("parent_episode_id") or task["episode_id"]
                if not old or feedback_id not in old["applied_events"]:
                    review.update(id=task["unit_id"], parent_episode_id=parent, session_id=task["session_id"])
                    self.save(owner, "review", task["unit_id"], review)
            return self.save(owner, "task", task_id, task)

    def probe_task(self, owner, task_id):
        with self.store.transaction():
            parent = self.get(owner, "task", task_id)
            if parent["state"] not in ("assisted_complete", "verified_complete"):
                raise ValueError("先完成并确认当前练习反馈")
            if parent.get("next_task_id"):
                return self.get(owner, "task", parent["next_task_id"])
            record_id = uuid.uuid4().hex
            task = {"id": record_id, "kind": "review", "title": "独立检验：换一道求根题",
                    "reason": "用新的初值与方程检查迁移；首次提交单独记录", "unit_id": parent["unit_id"],
                    "state": "planned", "graph_revision": self.revision(), "content_version": CONTENT_VERSION,
                    "study_session_id": parent.get("study_session_id", f"legacy:{parent['session_id']}"),
                    "parent_episode_id": parent["episode_id"], "session_id": parent["session_id"]}
            self.save(owner, "task", record_id, task)
            parent["next_task_id"] = record_id
            self.save(owner, "task", task_id, parent)
            return self.start(owner, record_id)

    def complete_reading(self, owner, task_id):
        with self.store.transaction():
            task = self.get(owner, "task", task_id)
            if task["kind"] != "reading":
                raise ValueError("只有阅读任务可标记已读")
            task["state"] = "read_complete"
            return self.save(owner, "task", task_id, task)

    def reading_units(self):
        result = []
        for unit_id, card in CARDS.items():
            unit = self.course.graph_repo.get_unit(unit_id)
            if not unit or unit.review_status != "verified":
                continue
            quote = unit.content
            result.append({"id": unit.id, "title": unit.title, "quote": quote, "latex": unit.latex,
                           "source_kind": "curated_course_pack", "source_span": unit.source_span,
                           "source_document_id": unit.source_document_id, "page_start": unit.page_start,
                           "source_hash": digest(quote), "graph_revision": self.revision(),
                           "conditions": card["conditions"], "condition_hash": digest(card["conditions"]),
                           "question": card["question"], "options": card["options"],
                           "content_version": CONTENT_VERSION, "review_status": "development_card"})
        return result

    def condition(self, owner, unit_id, option, source_hash):
        unit = next((u for u in self.reading_units() if u["id"] == unit_id), None)
        if not unit:
            raise KeyError(unit_id)
        if source_hash != unit["source_hash"]:
            raise ValueError("来源内容已更新，请刷新后重新阅读")
        card = CARDS[unit_id]
        if not 0 <= option < len(card["options"]):
            raise ValueError("无效选项")
        return {"reference_match": option == card["answer"], "explanation": card["explanation"],
                "source_hash": source_hash, "evidence_kind": "assisted_condition_check", "independent_success": False}

    def document(self, owner, document_id):
        doc = self.repository.get_document(document_id, owner)
        text = self.repository.get_document_markdown(document_id, owner) if doc else None
        if text is None:
            raise KeyError(document_id)
        if len(text) > 2_000_000:
            raise ValueError("文档超过伴读首版范围，请拆分章节")
        # Slice original markdown, never concatenate overlapping retrieval chunks.
        boundaries = [m.start() for m in re.finditer(r"(?m)^#{1,6} .+$", text)]
        starts = sorted(set([0, *boundaries, *range(0, len(text), 6000)]))
        sections = [{"id": str(i), "start": start, "end": end, "quote": text[start:end],
                     "title": text[start:end].splitlines()[0][:120] if text[start:end] else "正文"}
                    for i, (start, end) in enumerate(zip(starts, [*starts[1:], len(text)])) if end > start]
        return {"id": document_id, "filename": doc["filename"], "source_hash": digest(text), "sections": sections}

    def lab(self, owner, request):
        with self.store.transaction():
            # Re-check before cache reuse: a new assessment can lock old help.
            assert_reference_help_allowed(owner, self.course)
            old = self.store.learning_record(owner, self.course_id, "lab", request.request_id)
            input_hash = digest(request.model_dump())
            if old:
                if old["input_hash"] != input_hash:
                    raise ValueError("同一请求标识不能更改参数")
                return old
            result = run_reference(request)
            result.update(id=request.request_id, input_hash=input_hash, parameters=request.attempt.model_dump(), max_iterations=request.max_iterations,
                          prediction=request.prediction, graph_revision=self.revision(), created_at=datetime.now(timezone.utc).isoformat())
            return self.save(owner, "lab", request.request_id, result)

    def lab_run(self, owner, run_id):
        with self.store.transaction():
            assert_reference_help_allowed(owner, self.course)
            return self.get(owner, "lab", run_id)

    def lab_runs(self, owner):
        with self.store.transaction():
            assert_reference_help_allowed(owner, self.course)
            return self.store.learning_records(owner, self.course_id, "lab")[-20:]

    def save_reading_note(self, owner, request_id, source_id, source_hash, section_id, content):
        with self.store.transaction():
            if source_id in CARDS:
                source = next((u for u in self.reading_units() if u["id"] == source_id), None)
                if not source:
                    raise KeyError(source_id)
                quote = source["quote"]
            else:
                source = self.document(owner, source_id)
                section = next((s for s in source["sections"] if s["id"] == section_id), None)
                if not section:
                    raise KeyError(section_id)
                quote = section["quote"]
            if source_hash != source["source_hash"]:
                raise ValueError("来源内容已变更，不能将旧笔记挂到新版本")
            value = {"id": request_id, "source_id": source_id, "source_hash": source_hash,
                     "section_id": section_id, "quote": quote, "content": content,
                     "created_at": datetime.now(timezone.utc).isoformat()}
            old = self.store.learning_record(owner, self.course_id, "reading_note", request_id)
            if old:
                if any(old[k] != value[k] for k in ("source_id", "source_hash", "section_id", "content")):
                    raise ValueError("笔记请求标识已使用")
                return old
            return self.save(owner, "reading_note", request_id, value)

    def assessment_public(self, value):
        result = {key: value[key] for key in ("id", "state", "answers", "created_at", "content_version", "graph_revision")}
        result["mode"] = "chapter_diagnostic_training"
        result["grading_version"] = ASSESSMENT_VERSION
        result["independent_success"] = False
        result["questions"] = [{"id": q[0], "prompt": q[1], "options": q[2]} for q in value["questions"]]
        if value["state"] == "completed":
            result["feedback"] = [{"id": q[0], "reference_match": value["answers"].get(q[0]) == q[3], "reference_answer": q[3], "explanation": q[4], "unit_id": q[5]} for q in value["questions"]]
            result["reference_matches"] = sum(f["reference_match"] for f in result["feedback"])
            result["score"] = {"correct": result["reference_matches"], "total": len(value["questions"]),
                               "percentage": round(100 * result["reference_matches"] / len(value["questions"]))}
            result["review_units"] = list(dict.fromkeys(f["unit_id"] for f in result["feedback"] if not f["reference_match"]))
        return result

    def new_assessment(self, owner):
        with self.store.transaction():
            existing = next((a for a in self.store.learning_records(owner, self.course_id, "assessment") if a["state"] == "in_progress"), None)
            if existing:
                return self.assessment_public(existing)
            record_id = uuid.uuid4().hex
            value = {"id": record_id, "state": "in_progress", "answers": {}, "questions": QUESTIONS,
                     "created_at": datetime.now(timezone.utc).isoformat(), "content_version": ASSESSMENT_VERSION, "graph_revision": self.revision()}
            self.save(owner, "assessment", record_id, value)
            return self.assessment_public(value)

    def answer_assessment(self, owner, record_id, question_id, option):
        with self.store.transaction():
            value = self.get(owner, "assessment", record_id)
            if value["state"] != "in_progress":
                raise ValueError("已交卷，答案不能修改")
            question = next((q for q in value["questions"] if q[0] == question_id), None)
            if not question or not 0 <= option < len(question[2]):
                raise ValueError("无效题目或选项")
            # First valid response is fixed; repeated identical requests are safe.
            if question_id in value["answers"] and value["answers"][question_id] != option:
                raise ValueError("首次有效作答已保存，不能覆盖；可在下一份自检中重试")
            value["answers"][question_id] = option
            self.save(owner, "assessment", record_id, value)
            return self.assessment_public(value)

    def submit_assessment(self, owner, record_id):
        with self.store.transaction():
            value = self.get(owner, "assessment", record_id)
            if value["state"] not in ("in_progress", "completed"):
                raise ValueError("已结束的自检不能交卷计分")
            if len(value["answers"]) != len(value["questions"]):
                raise ValueError("请完成全部题目再交卷")
            value["state"] = "completed"
            self.save(owner, "assessment", record_id, value)
            return self.assessment_public(value)

    def end_assessment(self, owner, record_id):
        with self.store.transaction():
            value = self.get(owner, "assessment", record_id)
            if value["state"] == "completed":
                raise ValueError("已交卷的记录保留，不改为弃测")
            value["state"] = "abandoned"
            self.save(owner, "assessment", record_id, value)
            return self.assessment_public(value)

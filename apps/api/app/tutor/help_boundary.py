"""One owner-scoped boundary for reference help during assessments/probes."""

def assert_reference_help_allowed(owner, course=None, allowed_probe_id=None):
    if course is None:
        from app.knowledge.course_service import get_course_service
        course = get_course_service("numerical_analysis")
    if any(record.get("state") == "in_progress" for record in
           course.store.learning_records(owner, course.course_id, "assessment")):
        raise ValueError("请先完成或结束当前章节自检，再请求新的参考帮助。")
    pending = []
    for event in course.store.list_events(owner, course.course_id):
        if event["event_type"] == "probe_issued":
            episode = course.store.load_episode(event["payload"]["episode_id"])
            if episode and not any(a["acknowledged"] for a in episode["attempts"]):
                pending.append(episode["episode_id"])
    if pending and allowed_probe_id not in pending:
        raise ValueError("请先到今日学习完成并确认当前独立检验，再请求新的讲解、练习或笔记帮助。")

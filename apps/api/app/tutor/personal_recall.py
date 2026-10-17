"""Small owner-scoped recall of confirmed personal judgments, never course facts."""
import json
import re
from app.tutor.explorations import Explorations, PersonalNode, KIND, VERSION
from app.tutor.learning_workspace import digest
from app.tutor.help_boundary import assert_reference_help_allowed

TOPICS = (
    ("gauss", "gs", "对角占优", "谱半径", "线性迭代"),
    ("newton", "牛顿", "求根", "吸引域"),
    ("积分", "simpson", "梯形", "步长", "误差估计"),
)


def topics(text):
    text = text.lower()
    return {i for i, words in enumerate(TOPICS) if any(w in text for w in words)}


def select_personal_context(workspace, owner, question, *, limit=2):
    """At most two relations/records and 7 KiB. No unrelated or stale fallback."""
    assert_reference_help_allowed(owner, workspace.course)
    service = Explorations(workspace)
    selected = []
    query_topics = topics(question)
    # Store queries are owner/course/kind scoped. Pending/rejected proposals never enter graph.
    values = workspace.store.learning_records(owner, workspace.course_id, KIND)[-50:]
    ranked = []
    for value in values:
        if value.get("schema_version") != VERSION:
            continue
        nodes = {n["id"]: n for n in value["graph"]["nodes"]}
        for edge in value["graph"]["edges"]:
            pair = [nodes[edge[k]] for k in ("source", "target")]
            text = " ".join([value["claim"], value["history"][0]["claim"], *(n["label"] for n in pair), edge["reason"]])
            # A topic match alone is insufficient; require an explicit concept overlap.
            labels = [n["label"].strip().lower() for n in pair]
            explicit = any(len(label) >= 2 and label in question.lower() for label in labels)
            shared = query_topics & topics(text)
            if query_topics and topics(text) and not shared:
                continue
            tokens = re.findall(r"[a-zA-Z]{3,}|[\u4e00-\u9fff]{2,}", question.lower())
            overlap = sum(len(t) >= 3 and t in text.lower() for t in tokens)
            if not explicit and not (shared and overlap):
                continue
            sources = []
            try:
                for node in pair:
                    source = PersonalNode.model_validate(node).source_ref
                    if source:
                        bound = service.bind(owner, source)
                        if source.kind == "course":
                            saved = workspace.store.load_graph(workspace.course_id) or {}
                            unit = next(u for u in saved.get("data", {}).get("units", []) if u["id"] == source.unit_id)
                            bound["conditions"] = [str(c)[:300] for c in unit.get("conditions", [])[:3]]
                        sources.append(bound)
            except (ValueError, KeyError):
                continue
            ranked.append((int(explicit) * 4 + len(shared) + overlap, value["updated_at"], value, edge, pair, sources))
    seen = set()
    for score, _, value, edge, pair, sources in sorted(ranked, key=lambda r: (r[0], r[1]), reverse=True):
        if value["id"] in seen:
            continue
        experiments = []
        unavailable_experiments = []
        # Reuse the existing reference validation/recalculation, never trust saved display rows.
        from app.tutor.exploration_advice import checked_experiment
        relevant_refs = [r for r in value["runs"] if not query_topics or
                         {"linear_lab": 0, "root_lab": 1, "integration_lab": 2}.get(r["kind"]) in query_topics]
        for ref in relevant_refs[-1:]:
            try:
                experiments.append(checked_experiment(workspace, owner, ref))
            except (ValueError, KeyError):
                unavailable_experiments.append({"ref": ref, "state": "unavailable_or_changed", "reason": "原版本不可引用；没有改用其他计算"})
        revised = [h for h in value["history"] if h["action"] == "revise"][-1:]
        entry = {
            "id": f"personal:{len(selected)}", "exploration_id": value["id"],
            "revision": value["revision"], "relation_id": edge["id"],
            "relation_version": digest({"edge": edge, "nodes": pair}),
            "authority": "student_confirmed_unreviewed",
            "selection_reason": "当前问题明确涉及既往关系中的概念" if score >= 4 else "当前问题与旧判断共享数值方法和具体表述",
            "original_claim": value["history"][0]["claim"][:500],
            "current_claim": value["claim"][:500],
            "revisions": [{"revision": h["revision"], "claim": h["claim"][:500], "reason": h["payload"]["reason"][:300]} for h in revised],
            "relation": {**edge, "reason": edge["reason"][:400]},
            "nodes": [{**n, "description": n.get("description", "")[:150]} for n in pair],
            "evidence_refs": sources, "experiments": experiments,
            "unavailable_experiments": unavailable_experiments,
            "next_question": f"你曾用“{edge['reason'][:150]}”联系{pair[0]['label']}与{pair[1]['label']}；这次还满足同样条件吗？",
        }
        if len(json.dumps([*selected, entry], ensure_ascii=False).encode()) > 7168:
            continue
        selected.append(entry)
        seen.add(value["id"])
        if len(selected) >= limit:
            break
    return selected


def validate_personal_context(workspace, owner, selected):
    """Recheck identity/version/sources before delivery; never silently choose another source."""
    service = Explorations(workspace)
    for entry in selected:
        value = service.get(owner, entry["exploration_id"])
        if value["revision"] != entry["revision"]:
            raise ValueError("召回的私人探索已更新，请重新提问以核对当前版本")
        for source in entry["evidence_refs"]:
            from pydantic import TypeAdapter
            from app.tutor.explorations import Source
            service.bind(owner, TypeAdapter(Source).validate_python(source["ref"]))
        for run in entry["experiments"]:
            from app.tutor.exploration_advice import checked_experiment
            if checked_experiment(workspace, owner, run["ref"]) != run:
                raise ValueError("召回的实验版本已变化")

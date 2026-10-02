"""Deterministic review policy. Unknown outcomes cannot advance learning."""
from datetime import datetime, timedelta, timezone

POLICY_VERSION = "review-v1"
INTERVALS = (1, 3, 7, 14)


def advance_review(state: dict | None, outcome: str, event_id: str, session_id: str, now: datetime) -> dict | None:
    if outcome == "unknown":
        return state
    result = dict(state or {"stage": -1, "applied_events": [], "last_session_id": None})
    if event_id in result["applied_events"]:
        return result
    result["applied_events"] = [*result["applied_events"], event_id]
    if outcome == "independent_probe_success":
        if result.get("last_independent_session_id") == session_id:
            return result
        result["stage"] = min(3, result["stage"] + 1)
        result["last_independent_session_id"] = session_id
        days = INTERVALS[max(0, result["stage"])]
    elif outcome == "failed":
        result["stage"], days = -1, 1
    else:
        days = 1
    result.update(due_at=(now.astimezone(timezone.utc) + timedelta(days=days)).isoformat(),
                  last_session_id=session_id, last_event_id=event_id, policy_version=POLICY_VERSION)
    return result

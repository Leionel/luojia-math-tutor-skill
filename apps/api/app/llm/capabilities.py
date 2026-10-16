"""Exact operator-declared capability bindings; unknown endpoints stay unknown."""
import hashlib
import json
from datetime import datetime


def capability(settings, model=None):
    key = model or settings.llm_model
    unknown = {"tool_calls": None, "stream_usage": None, "streaming": None,
               "source": "unknown", "checked_at": None, "input_token_limit": None,
               "output_token_limit": None}
    try:
        base, resolved = settings.resolve_request(model)
        data = json.loads(settings.llm_capabilities_json)
        entry = data.get(key) if isinstance(data, dict) else None
        if not isinstance(entry, dict) or entry.get("resolved_model") != resolved or entry.get("base_url_sha256") != hashlib.sha256(base.rstrip('/').encode()).hexdigest():
            return unknown
        if entry.get("source") not in {"operator_verified", "offline_fixture"}:
            return unknown
        checked = datetime.fromisoformat(entry["checked_at"])
        if checked.tzinfo is None:
            return unknown
        fields = {k: entry.get(k) for k in ("tool_calls", "stream_usage", "streaming")}
        if any(v is not None and type(v) is not bool for v in fields.values()):
            return unknown
        for name in ("input_token_limit", "output_token_limit"):
            value = entry.get(name)
            fields[name] = value if type(value) is int and 1 <= value <= 1000000 else None
        return {**unknown, **fields, "source": entry["source"], "checked_at": checked.isoformat()}
    except (ValueError, TypeError, KeyError):
        return unknown


def tools_available(settings, model=None):
    cap = capability(settings, model)
    return settings.typed_math_tools_enabled and cap["tool_calls"] is True and cap["streaming"] is True

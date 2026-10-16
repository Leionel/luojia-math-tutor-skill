"""Strict assembly of a single Chat Completions native function request."""
import json
from dataclasses import dataclass, field

from app.agents.typed_tools import ToolCall, MAX_INPUT
from app.llm.completion_protocol import ModelCompletionError


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate tool argument")
        result[key] = value
    return result


@dataclass
class ModelTurn:
    content: str = ""
    calls: list[ToolCall] = field(default_factory=list)
    model_call_id: str | None = None


class TurnAssembler:
    def __init__(self):
        self.content = ""
        self.call = None
        self.finish = None
        self.bytes = 0

    def feed(self, choice):
        if self.finish is not None:
            raise ModelCompletionError("model_response_invalid")
        delta = choice.get("delta")
        if not isinstance(delta, dict):
            raise ModelCompletionError("model_response_invalid")
        text = delta.get("content")
        if text is not None:
            if not isinstance(text, str): raise ModelCompletionError("model_response_invalid")
            self.content += text
            if len(self.content.encode()) > 131072: raise ModelCompletionError("model_output_truncated")
        parts = delta.get("tool_calls")
        if parts is not None:
            if not isinstance(parts, list) or len(parts) != 1:
                raise ModelCompletionError("model_response_invalid")
            part = parts[0]
            if not isinstance(part, dict) or type(part.get("index")) is not int or part["index"] != 0:
                raise ModelCompletionError("model_response_invalid")
            if set(part)-{"index", "id", "type", "function"} or part.get("type", "function") not in {"function", None}:
                raise ModelCompletionError("model_response_invalid")
            if self.call is None: self.call = {"id": "", "name": "", "arguments": ""}
            if part.get("id") is not None:
                if not isinstance(part["id"], str) or (self.call["id"] and self.call["id"] != part["id"]): raise ModelCompletionError("model_response_invalid")
                self.call["id"] = part["id"]
            function = part.get("function", {})
            if not isinstance(function, dict) or set(function)-{"name", "arguments"}:
                raise ModelCompletionError("model_response_invalid")
            for key in ("name", "arguments"):
                if function.get(key) is not None:
                    value = function[key]
                    if not isinstance(value, str): raise ModelCompletionError("model_response_invalid")
                    self.bytes += len(value.encode())
                    if self.bytes > MAX_INPUT: raise ModelCompletionError("model_response_invalid")
                    self.call[key] += value
        reason = choice.get("finish_reason")
        if reason is not None:
            if reason not in {"stop", "tool_calls"}:
                from app.llm.completion_protocol import validate_finish_reason
                validate_finish_reason(reason)
            self.finish = reason

    def result(self):
        if self.finish is None:
            raise ModelCompletionError("model_stream_incomplete")
        if self.call is None:
            if self.finish != "stop" or not self.content.strip(): raise ModelCompletionError("model_empty_output")
            return ModelTurn(self.content)
        if self.finish != "tool_calls": raise ModelCompletionError("model_response_invalid")
        try:
            args = json.loads(self.call["arguments"], object_pairs_hook=unique_object,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            call = ToolCall(call_id=self.call["id"], name=self.call["name"], arguments=args)
        except (ValueError, TypeError, RecursionError):
            raise ModelCompletionError("model_response_invalid") from None
        return ModelTurn(self.content, [call])

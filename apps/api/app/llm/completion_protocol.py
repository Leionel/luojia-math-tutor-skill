"""Provider completion failures with bounded, public error messages."""


class ModelCompletionError(RuntimeError):
    MESSAGES = {
        "model_not_configured": "模型服务尚未配置，本轮没有生成回答。",
        "model_stream_incomplete": "模型连接提前结束，回答尚未完成，请重试。",
        "model_output_truncated": "模型输出达到长度限制，回答尚未完成，请缩小问题范围后重试。",
        "model_output_filtered": "模型服务未能返回完整内容，请调整问题后重试。",
        "model_tool_call_unsupported": "模型返回了当前通道不支持的工具调用，本轮未完成。",
        "model_response_invalid": "模型服务返回格式异常，本轮未完成，请重试。",
        "model_provider_error": "模型服务报告生成失败，请稍后重试。",
        "model_empty_output": "模型未返回可交付的正文，请重试。",
    }

    def __init__(self, code: str):
        self.code = code if code in self.MESSAGES else "model_response_invalid"
        super().__init__(self.MESSAGES[self.code])


def validate_finish_reason(reason: object) -> bool:
    """Return whether this is a successful terminal signal, never an idle guess."""
    if reason is None:
        return False
    if reason == "stop":
        return True
    code = {
        "length": "model_output_truncated",
        "content_filter": "model_output_filtered",
        "tool_calls": "model_tool_call_unsupported",
        "function_call": "model_tool_call_unsupported",
    }.get(reason) if isinstance(reason, str) else None
    raise ModelCompletionError(code or "model_response_invalid")

"""Execution evidence, deliberately separate from mathematical validity."""
from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class ToolExecutionResult:
    status: Literal["succeeded", "failed", "timeout", "rejected", "unavailable"]
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    error_code: str | None = None
    duration_ms: float = 0.0

    @property
    def execution_succeeded(self) -> bool:
        return self.status == "succeeded" and self.exit_code == 0

    @property
    def has_output(self) -> bool:
        return bool(self.stdout.strip())

    def to_dict(self) -> dict:
        return {**asdict(self), "execution_succeeded": self.execution_succeeded,
                "has_output": self.has_output, "validation_scope": "execution_only"}

    def to_legacy_text(self) -> str:
        if not self.execution_succeeded:
            return self.stderr if self.stderr.startswith("Error:") else f"Error: {self.stderr or self.error_code or self.status}"
        parts = [f"Output:\n{self.stdout}"] if self.stdout else []
        if self.stderr:
            parts.append(f"Stderr:\n{self.stderr}")
        return "\n".join(parts) or "Code executed successfully with no output."

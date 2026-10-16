"""Small private request contract, validated before loading the symbolic engine."""
from dataclasses import dataclass

STEP_CHECK_VERSION = "step-v2"


@dataclass(frozen=True)
class StepCheckRequest:
    version: str
    message: str

    def __post_init__(self):
        if (type(self.version) is not str or self.version != STEP_CHECK_VERSION
                or type(self.message) is not str or not 1 <= len(self.message) <= 4096):
            raise ValueError("invalid_step_request")

    @classmethod
    def from_packet(cls, packet):
        if type(packet) is not dict or set(packet) != {"version", "message"}:
            raise ValueError("invalid_step_request_fields")
        return cls(**packet)

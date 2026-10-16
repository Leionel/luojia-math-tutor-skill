"""Disabled execution gate: malicious submissions remain text in static review.

These tests are not a sandbox certification or resource isolation benchmark.
"""

import pytest
from test_learning_workspace import workspace, code_request
from app.tutor.learning_extensions import submit_code


@pytest.mark.parametrize(
    "code",
    [
        'import subprocess\nsubprocess.run(["whoami"])',
        'import socket\nsocket.create_connection(("example.invalid",443))',
        "while True:\n    pass",
        "x=[0]*(10**12)",
        "import os\nos.fork()",
        '__import__("builtins").exec("print(1)")',
    ],
)
def test_student_payload_is_never_executed(workspace, monkeypatch, code):
    import socket, subprocess

    def forbidden(*a, **kw):
        raise AssertionError("static submission attempted execution/network")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    result = submit_code(
        workspace, "alice", code_request().model_copy(update={"code": code})
    )
    assert result["code_executed"] is False
    assert result["independent_success"] is False

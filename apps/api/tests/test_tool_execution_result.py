import asyncio
import subprocess
import threading
from pathlib import Path

import pytest

from app.agents.code_executor import execute_python_result


@pytest.mark.asyncio
async def test_stdout_error_word_does_not_turn_success_into_failure():
    result = await execute_python_result("print('Error: is just a label')")
    assert result.execution_succeeded and result.has_output
    assert result.stdout == "Error: is just a label"
    assert result.to_dict()["validation_scope"] == "execution_only"


@pytest.mark.asyncio
async def test_exit_code_and_empty_output_are_distinct_evidence():
    failed = await execute_python_result("print(1 / 0)")
    assert failed.status == "failed" and failed.exit_code != 0
    assert not failed.execution_succeeded
    empty = await execute_python_result("x = 2")
    assert empty.execution_succeeded and not empty.has_output


@pytest.mark.asyncio
async def test_rejected_code_never_spawns_a_child(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("rejected code reached Popen")
    monkeypatch.setattr("app.agents.code_executor.subprocess.Popen", unexpected)
    result = await execute_python_result("open('private.txt')")
    assert result.status == "rejected" and result.error_code == "code_rejected"


class ControlledProcess:
    """A bounded blocking child substitute, without external programs or sleeps."""
    def __init__(self, argv, **kwargs):
        self.path = Path(argv[-1])
        self.started = threading.Event()
        self.stopped = threading.Event()
        self.returncode = None
        self.kills = 0
        self.finished = False

    def communicate(self, timeout=None):
        self.started.set()
        if not self.stopped.wait(timeout if timeout is not None else 5):
            raise subprocess.TimeoutExpired("math-child", timeout)
        self.finished = True
        return "", ""

    def kill(self):
        self.kills += 1
        self.returncode = -1
        self.stopped.set()

    def poll(self):
        return self.returncode

    def wait(self):
        assert self.stopped.wait(5)
        return self.returncode


@pytest.mark.asyncio
async def test_cancel_kills_owned_child_finishes_communication_and_removes_script(monkeypatch):
    children = []
    def spawn(*args, **kwargs):
        child = ControlledProcess(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr("app.agents.code_executor.subprocess.Popen", spawn)
    task = asyncio.create_task(execute_python_result("print(2)"))
    # Wait for the actual spawn boundary, then for the worker to enter communicate.
    while not children:
        await asyncio.sleep(0)
    child = children[0]
    assert await asyncio.wait_for(asyncio.to_thread(child.started.wait, 5), 6)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 6)
    assert child.kills == 1 and child.finished
    assert not child.path.exists()


@pytest.mark.asyncio
async def test_timeout_is_not_success_and_cleans_up_child(monkeypatch):
    children = []
    def spawn(*args, **kwargs):
        child = ControlledProcess(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr("app.agents.code_executor.subprocess.Popen", spawn)
    result = await execute_python_result("print(2)", timeout=1)
    assert result.status == "timeout" and result.error_code == "tool_timeout"
    assert not result.execution_succeeded
    assert children[0].kills == 1 and children[0].finished
    assert not children[0].path.exists()


@pytest.mark.asyncio
async def test_stderr_warning_does_not_override_zero_exit(monkeypatch):
    class WarningProcess(ControlledProcess):
        def communicate(self, timeout=None):
            self.returncode = 0
            return "4", "a nonfatal warning"
    monkeypatch.setattr("app.agents.code_executor.subprocess.Popen", WarningProcess)
    result = await execute_python_result("print(4)")
    assert result.execution_succeeded and result.stderr == "a nonfatal warning"

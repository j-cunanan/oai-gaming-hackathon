import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from repro.models import Action


@pytest.fixture
def driver(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "infra/docker/worker.py"
    spec = importlib.util.spec_from_file_location("desktop_input_test_worker", path)
    worker = importlib.util.module_from_spec(spec)
    with patch.object(Path, "mkdir"):
        spec.loader.exec_module(worker)
    events = []

    def operation(name):
        def call(*args, **kwargs):
            events.append((name, args, kwargs))

        return call

    pg = SimpleNamespace(
        KEYBOARD_KEYS=["ctrl", "shift", "w", "a", "esc", "enter", "win"],
        **{
            name: operation(name)
            for name in [
                "keyDown",
                "keyUp",
                "click",
                "doubleClick",
                "hotkey",
                "write",
                "moveTo",
                "scroll",
                "mouseDown",
                "mouseUp",
            ]
        },
    )
    monkeypatch.setitem(sys.modules, "pyautogui", pg)
    monkeypatch.setattr(worker.time, "sleep", operation("sleep"))
    monkeypatch.setattr(worker, "observe", lambda: {"observed": True})
    return worker, pg, events


@pytest.mark.parametrize("action", ["click", "double_click", "move", "scroll"])
def test_pointer_modifier_is_held_across_the_action_and_released_before_settling(driver, action):
    worker, _, events = driver
    result = worker.action(
        Action(action=action, x=30, y=40, keys=["control"], scroll_y=2).model_dump()
    )
    assert result == {"observed": True}
    assert events[0] == ("keyDown", ("ctrl",), {})
    assert events[-2:] == [("keyUp", ("ctrl",), {}), ("sleep", (0.5,), {})]
    assert any(name in {"click", "doubleClick", "moveTo"} for name, _, _ in events[1:-2])


def test_timed_movement_uses_key_down_and_up_with_a_separate_settling_wait(driver):
    worker, _, events = driver
    worker.action(
        Action(action="keypress", keys=["w"], hold_seconds=0.75, seconds=0.2).model_dump()
    )
    assert events == [
        ("keyDown", ("w",), {}),
        ("sleep", (0.75,), {}),
        ("keyUp", ("w",), {}),
        ("sleep", (0.2,), {}),
    ]


def test_existing_momentary_keypress_keeps_its_hotkey_behavior(driver):
    worker, _, events = driver
    worker.action(Action(action="keypress", keys=["ctrl", "a"]).model_dump())
    assert events == [("hotkey", ("ctrl", "a"), {}), ("sleep", (0.5,), {})]


def test_mouse_and_modifiers_are_released_when_a_held_action_fails(driver, monkeypatch):
    worker, pg, events = driver

    def fail(**kwargs):
        events.append(("mouseDown", (), kwargs))
        raise RuntimeError("Desktop input failed")

    monkeypatch.setattr(pg, "mouseDown", fail)
    with pytest.raises(RuntimeError, match="Desktop input failed"):
        worker.action(
            Action(action="click", x=30, y=40, keys=["ctrl"], hold_seconds=1).model_dump()
        )
    assert events[-2:] == [("mouseUp", (), {"button": "left"}), ("keyUp", ("ctrl",), {})]


def test_bad_modifier_is_rejected_before_any_input(driver):
    worker, _, events = driver
    with pytest.raises(ValueError, match="Unknown keyboard key"):
        worker.action(Action(action="click", x=30, y=40, keys=["not-a-key"]).model_dump())
    assert events == []


@pytest.mark.parametrize(
    "args", [{"action": "wait", "hold_seconds": 1}, {"action": "type", "keys": ["ctrl"]}]
)
def test_unsupported_timing_or_modifier_combinations_are_explicit(args):
    with pytest.raises(ValidationError):
        Action(**args)

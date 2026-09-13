import base64
import time

from repro.models import Action, Case
from repro.storage.store import Store


class Recorder:
    def __init__(self, store: Store, case: Case, sandbox):
        self.store, self.case, self.sandbox = store, case, sandbox
        self.actions: list[Action] = []
        self.last_screenshot: str | None = None
        self.previous_log = ""

    def capture(self, observation: dict, label="screen") -> dict:
        screenshot = observation["screenshot"]
        artifact = self.store.artifact(
            self.case.id, f"{label}.png", base64.b64decode(screenshot), "image/png"
        )
        self.last_screenshot = self.case.latest_screenshot = artifact
        logs = observation.get("logs", "")
        log_delta = logs[len(self.previous_log) :] if logs.startswith(self.previous_log) else logs
        self.previous_log = logs
        log_artifact = (
            self.store.artifact(self.case.id, f"{label}.log", log_delta) if log_delta else None
        )
        self.store.save(self.case)
        return {
            **observation,
            "screenshot_artifact": artifact,
            "log_artifact": log_artifact,
            "log_delta": log_delta,
        }

    async def observe(self):
        result = self.capture(await self.sandbox.observe())
        self.store.save(
            self.case, "observation", {k: v for k, v in result.items() if k != "screenshot"}
        )
        return result

    async def act(self, action: Action, *, phase="investigation"):
        before = self.last_screenshot
        observation = self.capture(await self.sandbox.action(action), phase)
        self.actions.append(action)
        self.store.save(
            self.case,
            "action",
            {
                "index": len(self.actions),
                "phase": phase,
                "action": action.model_dump(),
                "timestamp": time.time(),
                "screenshot_before": before,
                "screenshot_after": self.last_screenshot,
                "log_artifact": observation["log_artifact"],
                "process": observation.get("process"),
            },
        )
        return observation

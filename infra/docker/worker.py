"""Persistent JSON-lines desktop driver inside one disposable game container."""

import base64
import io
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

RUNTIME = Path("/workspace/runtime")
RUNTIME.mkdir(exist_ok=True)
GAME = None
SCREEN = None


def save_state(state):
    temporary = RUNTIME / "process.json.tmp"
    temporary.write_text(json.dumps(state))
    temporary.replace(RUNTIME / "process.json")


def screenshot():
    global SCREEN
    import mss
    from PIL import Image

    if SCREEN is None:
        SCREEN = mss.mss()
    shot = SCREEN.grab({"top": 0, "left": 0, "width": 1280, "height": 720})
    output = io.BytesIO()
    # Lossless PNG; avoid expensive compression on the emulated worker CPU.
    Image.frombytes("RGB", shot.size, shot.rgb).save(output, format="PNG", compress_level=1)
    return base64.b64encode(output.getvalue()).decode()


def process_state():
    path = RUNTIME / "process.json"
    if not path.exists():
        return {"running": False, "exit_code": None, "launched": False}
    state = json.loads(path.read_text())
    if GAME is not None and state["pid"] == GAME.pid:
        state["exit_code"] = GAME.poll()
        save_state(state)
    if state.get("exit_code") is None:
        try:
            os.kill(state["pid"], 0)
            state["running"] = True
        except ProcessLookupError:
            state["running"] = False
    else:
        state["running"] = False
    state["launched"] = True
    return state


def observe():
    log = RUNTIME / "game.log"
    return {
        "screenshot": screenshot(),
        "process": process_state(),
        "logs": log.read_text(errors="replace")[-16000:] if log.exists() else "",
    }


def launch(args):
    global GAME
    if process_state()["running"]:
        raise ValueError("A game is already running; reset or terminate it first")
    env = os.environ.copy()
    env["XDG_DATA_HOME"] = "/workspace/runtime/profile/data"
    env["XDG_CONFIG_HOME"] = "/workspace/runtime/profile/config"
    with (RUNTIME / "game.log").open("w") as log:
        GAME = subprocess.Popen(
            args["argv"],
            cwd="/workspace/repo",
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    save_state({"pid": GAME.pid, "exit_code": None, "started_at": time.time()})
    return {"started": True}


def terminate():
    state = process_state()
    if state["running"]:
        try:
            os.killpg(state["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
    if GAME is not None:
        try:
            GAME.wait(timeout=1)
        except subprocess.TimeoutExpired:
            os.killpg(GAME.pid, signal.SIGKILL)
            GAME.wait()
        process_state()
    return {"terminated": True}


def action(args):
    import pyautogui as pg

    pg.FAILSAFE = False  # Dedicated Xvfb desktop, never the host desktop.
    pg.PAUSE = 0.12
    op = args["action"]
    if op not in {"click", "double_click", "keypress", "type", "scroll", "move", "wait"}:
        raise ValueError("Unsupported action")
    aliases = {"escape": "esc", "return": "enter", "control": "ctrl", "super": "win"}
    keys = [aliases.get(k.lower(), k.lower()) for k in args.get("keys", [])]
    if any(k not in pg.KEYBOARD_KEYS for k in keys):
        raise ValueError("Unknown keyboard key")
    if op == "keypress" and not keys:
        raise ValueError("keypress requires keys")
    hold = min(max(args.get("hold_seconds", 0), 0), 10)
    if hold and op not in {"click", "keypress"}:
        raise ValueError("hold_seconds applies only to click or keypress")
    if keys and op in {"type", "wait"}:
        raise ValueError("Use keypress or a pointer action for held keys")
    held = []
    try:
        # A modifier-click must hold its keys across the mouse event. Timed
        # keypresses likewise need keyDown/keyUp, not a momentary hotkey.
        if op != "keypress" or hold:
            for key in keys:
                held.append(key)
                pg.keyDown(key)
        if op == "click":
            button = args.get("button", "left")
            if hold:
                pg.moveTo(args["x"], args["y"])
                try:
                    pg.mouseDown(button=button)
                    time.sleep(hold)
                finally:
                    pg.mouseUp(button=button)
            else:
                pg.click(args["x"], args["y"], button=button)
        elif op == "double_click":
            pg.doubleClick(
                args["x"], args["y"], interval=0.1, button=args.get("button", "left")
            )
        elif op == "keypress":
            if hold:
                time.sleep(hold)
            else:
                pg.hotkey(*keys)
        elif op == "type":
            pg.write(args["text"], interval=0.01)
        elif op == "scroll":
            pg.moveTo(args["x"], args["y"])
            pg.scroll(args["scroll_y"])
        elif op == "move":
            pg.moveTo(args["x"], args["y"])
    finally:
        for key in reversed(held):
            pg.keyUp(key)
    # Recorded settling time is preserved; throughput improvements remove process overhead.
    time.sleep(min(max(args.get("seconds", 0.5), 0), 10))
    return observe()


def dispatch(operation, args):
    if operation == "ping":
        return {"protocol": 3}
    if operation == "launch":
        return launch(args)
    if operation == "terminate":
        return terminate()
    if operation == "observe":
        return observe()
    if operation == "action":
        return action(args)
    raise ValueError("Unknown operation")


def main():
    if sys.argv[1] == "serve":
        try:
            for line in sys.stdin:
                try:
                    request = json.loads(line)
                    result = dispatch(request["operation"], request.get("args", {}))
                    response = {"ok": True, "result": result}
                except Exception as exc:
                    response = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
                print(json.dumps(response), flush=True)
        finally:
            terminate()
    else:
        operation = sys.argv[1]
        result = dispatch(operation, json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
        if operation == "launch":
            GAME.wait()
            process_state()
        else:
            print(json.dumps(result))


if __name__ == "__main__":
    main()

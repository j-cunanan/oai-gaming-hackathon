"""Small JSON RPC executable inside the network-isolated game container."""
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


def screenshot():
    import mss
    from PIL import Image

    with mss.mss() as screen:
        shot = screen.grab({"top": 0, "left": 0, "width": 1280, "height": 720})
    output = io.BytesIO()
    Image.frombytes("RGB", shot.size, shot.rgb).save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode()


def process_state():
    path = RUNTIME / "process.json"
    if not path.exists():
        return {"running": False, "exit_code": None, "launched": False}
    data = json.loads(path.read_text())
    if data.get("exit_code") is None:
        try:
            os.kill(data["pid"], 0)
            data["running"] = True
        except ProcessLookupError:
            data["running"] = False
    else:
        data["running"] = False
    data["launched"] = True
    return data


def main():
    operation = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    if operation == "launch":
        (RUNTIME / "process.json").unlink(missing_ok=True)
        env = os.environ.copy()
        env["XDG_DATA_HOME"] = "/workspace/runtime/profile/data"
        env["XDG_CONFIG_HOME"] = "/workspace/runtime/profile/config"
        with (RUNTIME / "game.log").open("w") as log:
            proc = subprocess.Popen(args["argv"], cwd="/workspace/repo", env=env,
                                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            state = {"pid": proc.pid, "exit_code": None, "started_at": time.time()}
            (RUNTIME / "process.json").write_text(json.dumps(state))
            state["exit_code"] = proc.wait()
            (RUNTIME / "process.json").write_text(json.dumps(state))
        return
    if operation == "terminate":
        state = process_state()
        if state["running"]:
            try:
                os.killpg(state["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass
        result = {"terminated": True}
    elif operation == "observe":
        log = RUNTIME / "game.log"
        result = {"screenshot": screenshot(), "process": process_state(),
                  "logs": log.read_text(errors="replace")[-16000:] if log.exists() else ""}
    elif operation == "action":
        import pyautogui as pg

        pg.FAILSAFE = False  # Dedicated disposable Xvfb desktop, never the host desktop.
        pg.PAUSE = 0.12
        op = args["action"]
        if op == "click":
            pg.click(args["x"], args["y"], button=args.get("button", "left"))
        elif op == "double_click":
            pg.doubleClick(args["x"], args["y"], interval=0.1)
        elif op == "keypress":
            aliases = {"escape": "esc", "return": "enter", "control": "ctrl", "super": "win"}
            keys = [aliases.get(k.lower(), k.lower()) for k in args["keys"]]
            if any(k not in pg.KEYBOARD_KEYS for k in keys):
                raise ValueError("Unknown keyboard key")
            pg.hotkey(*keys)
        elif op == "type":
            pg.write(args["text"], interval=0.01)
        elif op == "scroll":
            pg.moveTo(args["x"], args["y"])
            pg.scroll(args["scroll_y"])
        elif op == "move":
            pg.moveTo(args["x"], args["y"])
        elif op != "wait":
            raise ValueError("Unsupported action")
        time.sleep(min(max(args.get("seconds", 0.5), 0), 10))
        result = {"ok": True}
    else:
        raise ValueError("Unknown operation")
    print(json.dumps(result))


if __name__ == "__main__":
    main()

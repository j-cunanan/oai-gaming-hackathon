import importlib.util
import json

from Xlib import XK, X, display

connection = display.Display()
window = connection.screen().root.create_window(
    100,
    100,
    300,
    200,
    0,
    connection.screen().root_depth,
    X.InputOutput,
    X.CopyFromParent,
    background_pixel=connection.screen().white_pixel,
    override_redirect=True,
    event_mask=X.KeyPressMask | X.KeyReleaseMask | X.ButtonPressMask | X.ButtonReleaseMask,
)
window.map()
window.set_input_focus(X.RevertToParent, X.CurrentTime)
connection.sync()
spec = importlib.util.spec_from_file_location("repro_worker", "/opt/repro/worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
worker.action({"action": "click", "x": 150, "y": 150, "keys": ["ctrl"], "seconds": 0})
worker.action({"action": "keypress", "keys": ["w"], "hold_seconds": 0.3, "seconds": 0})
connection.sync()
events = []
while connection.pending_events():
    event = connection.next_event()
    if event.type in (X.KeyPress, X.KeyRelease, X.ButtonPress, X.ButtonRelease):
        events.append(
            {"type": event.type, "detail": event.detail, "state": event.state, "time": event.time}
        )
press = next(e for e in events if e["type"] == X.ButtonPress)
wcode = connection.keysym_to_keycode(XK.string_to_keysym("w"))
wdown = next(e for e in events if e["type"] == X.KeyPress and e["detail"] == wcode)
wup = next(e for e in events if e["type"] == X.KeyRelease and e["detail"] == wcode)
elapsed = (wup["time"] - wdown["time"]) % 2**32
control = bool(press["state"] & X.ControlMask)
print(
    json.dumps(
        {
            "worker_protocol": worker.dispatch("ping", {}),
            "scope": "Actual X11 input events in a disposable desktop; no game or AI calls",
            "modifier_at_click": control,
            "held_w_ms": elapsed,
            "requested_hold_ms": 300,
            "passed": control and elapsed >= 300,
            "events": events,
        },
        indent=2,
    )
)
window.destroy()
connection.close()

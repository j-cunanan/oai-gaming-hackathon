"""Wait for Xvfb and, optionally, its window manager before launching the game."""

import sys
import time

from Xlib import display, error


def wait_desktop(require_wm=False, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        connection = None
        try:
            connection = display.Display()
            root = connection.screen().root
            if not require_wm or root.get_full_property(
                connection.intern_atom("_NET_SUPPORTING_WM_CHECK"), 0
            ):
                return
        except (error.DisplayConnectionError, error.ConnectionClosedError, OSError):
            pass
        finally:
            if connection is not None:
                connection.close()
        time.sleep(0.1)
    raise TimeoutError("Desktop window manager not ready" if require_wm else "Xvfb not ready")


if __name__ == "__main__":
    wait_desktop(require_wm="--wm" in sys.argv)

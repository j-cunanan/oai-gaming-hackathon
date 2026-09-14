#!/bin/sh
set -eu
touch /home/worker/.Xauthority
xauth add :99 . "$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
Xvfb :99 -screen 0 1280x720x24 -nolisten tcp -auth /home/worker/.Xauthority &
python3 /opt/repro/wait_desktop.py
openbox >/tmp/openbox.log 2>&1 &
exec sleep infinity

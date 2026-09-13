#!/bin/sh
set -eu
Xvfb :99 -screen 0 1280x720x24 -nolisten tcp -ac &
openbox >/tmp/openbox.log 2>&1 &
exec sleep infinity

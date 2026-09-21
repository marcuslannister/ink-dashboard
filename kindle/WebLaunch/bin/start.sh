#!/bin/sh
# WebLaunch start for Kindle Touch 5.3.7.3 (Mesquite).
# Mesquite renders bin/dash.html (config.xml content). start.sh probes which
# bridge address is reachable, then rewrites dash.html as a one-shot bootstrap
# page that redirects to the live URL. The bridge serves the Kindle scaling at
# /?k=1, and the page's own meta refresh keeps it updating every minute.
LOG=/mnt/us/extensions/WebLaunch/run.log
APP=/mnt/us/extensions/WebLaunch
# USB ethernet host first, then LAN. Edit if the Mac address changes.
USB_URL=http://192.168.15.201:8787/?k=1
LAN_URL=http://192.168.8.4:8787/?k=1
exec > "$LOG" 2>&1
echo "=== start ==="
sqlite3 /var/local/appreg.db "update properties set value='/usr/bin/mesquite -l com.PaulFreund.WebLaunch -c $APP/bin/' where handlerId='com.PaulFreund.WebLaunch' and name='command';"
if wget -q -T 5 -O /dev/null "$USB_URL"; then
	BRIDGE_URL="$USB_URL"
	echo "using usb"
else
	BRIDGE_URL="$LAN_URL"
	echo "using lan"
fi
printf '<!DOCTYPE html>\n<html><head><meta http-equiv="refresh" content="0; url=%s"></head><body></body></html>\n' "$BRIDGE_URL" > "$APP/bin/dash.html"
lipc-set-prop com.lab126.appmgrd stop "app://com.PaulFreund.WebLaunch"
sleep 1
lipc-set-prop com.lab126.winmgr orientationLock U
lipc-set-prop com.lab126.powerd preventScreenSaver 1
echo "start"
lipc-set-prop com.lab126.appmgrd start "app://com.PaulFreund.WebLaunch"
echo "EXIT: $?"

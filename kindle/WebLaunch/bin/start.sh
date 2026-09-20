#!/bin/sh
# WebLaunch start for Kindle Touch 5.3.7.3 (Mesquite).
# Fetches the bridge page, scales the 800x600 layout to 600px portrait, then starts the app.
LOG=/mnt/us/extensions/WebLaunch/run.log
DIR=/mnt/us/extensions/WebLaunch/bin
# USB ethernet host first, then LAN. Edit if the Mac address changes.
USB_URL=http://192.168.15.201:8787/
LAN_URL=http://192.168.8.4:8787/
exec > "$LOG" 2>&1
echo "=== start ==="
sqlite3 /var/local/appreg.db "update properties set value='/usr/bin/mesquite -l com.PaulFreund.WebLaunch -c /mnt/us/extensions/WebLaunch/bin/' where handlerId='com.PaulFreund.WebLaunch' and name='command';"
inject() {
	sed -e 's/<meta http-equiv="refresh" content="[0-9]*">//g' "$DIR/dash.next" > "$DIR/dash.html"
	sed -i 's|<style>|<style>html{overflow:hidden}body{-webkit-transform:scale(0.75);-webkit-transform-origin:0 0;}|' "$DIR/dash.html"
	sed -i 's|</head>|<script type="text/javascript">try{kindle.dev.setOrientation("portrait");}catch(e){}</script></head>|' "$DIR/dash.html"
}
if wget -O "$DIR/dash.next" "$USB_URL"; then
	inject
	echo "fetched usb"
elif wget -O "$DIR/dash.next" "$LAN_URL"; then
	inject
	echo "fetched lan"
else
	echo "wget failed, using existing dash.html"
fi
rm -f "$DIR/dash.next"
lipc-set-prop com.lab126.appmgrd stop "app://com.PaulFreund.WebLaunch"
sleep 1
lipc-set-prop com.lab126.winmgr orientationLock U
lipc-set-prop com.lab126.powerd preventScreenSaver 1
echo "start"
lipc-set-prop com.lab126.appmgrd start "app://com.PaulFreund.WebLaunch"
echo "EXIT: $?"

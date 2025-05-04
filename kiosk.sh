#!/usr/bin/env bash

# Prevent screen blanking
xset s noblank
xset s off

# Start xscreensaver (optional, for better touchscreen handling)
xscreensaver &

# Hide mouse cursor after 1s of inactivity
unclutter -idle 1 -root &

# Fix Chromium's restore popup
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/Default/Preferences
sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences

# Start Chromium in kiosk mode
exec chromium-browser --kiosk --noerrdialogs --disable-infobars --app=http://localhost:5000 
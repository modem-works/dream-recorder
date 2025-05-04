#!/usr/bin/env python3
import os
import sys
import subprocess

# Path to the wallpaper image (project root)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
WALLPAPER_PATH = os.path.join(PROJECT_ROOT, 'static', 'images', 'background', '0.jpg')

if not os.path.isfile(WALLPAPER_PATH):
    print(f"[ERROR] Wallpaper image not found at {WALLPAPER_PATH}")
    sys.exit(1)

# pcmanfm config path for LXDE/PIXEL
HOME = os.path.expanduser('~')
PCMANFM_CONF_DIR = os.path.join(HOME, '.config', 'pcmanfm', 'LXDE-pi')
PCMANFM_CONF_FILE = os.path.join(PCMANFM_CONF_DIR, 'desktop-items-0.conf')

os.makedirs(PCMANFM_CONF_DIR, exist_ok=True)

# Read or create config
config_lines = []
if os.path.exists(PCMANFM_CONF_FILE):
    with open(PCMANFM_CONF_FILE, 'r') as f:
        config_lines = f.readlines()
else:
    config_lines = ['[*]\n']

# Update or add wallpaper and wallpaper_mode
found_wallpaper = False
found_mode = False
for i, line in enumerate(config_lines):
    if line.startswith('wallpaper='):
        config_lines[i] = f'wallpaper={WALLPAPER_PATH}\n'
        found_wallpaper = True
    if line.startswith('wallpaper_mode='):
        config_lines[i] = 'wallpaper_mode=stretch\n'
        found_mode = True
if not found_wallpaper:
    config_lines.append(f'wallpaper={WALLPAPER_PATH}\n')
if not found_mode:
    config_lines.append('wallpaper_mode=stretch\n')

with open(PCMANFM_CONF_FILE, 'w') as f:
    f.writelines(config_lines)

print(f"[INFO] Wallpaper set to {WALLPAPER_PATH}")

# Try to reload the desktop (only works in a running desktop session)
try:
    subprocess.run(['pcmanfm', '--reconfigure'], check=True)
    print("[INFO] Desktop reloaded.")
except Exception as e:
    print(f"[WARN] Could not reload desktop automatically: {e}\nThe wallpaper will be set on next login.") 
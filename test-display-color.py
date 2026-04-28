#!/usr/bin/env python3
# Writes a color test pattern directly to /dev/fb0.
# If colors are correct you should see (top to bottom): RED, GREEN, BLUE, WHITE.
# If R and B are swapped you'll see: BLUE, GREEN, RED, WHITE.

import struct
import subprocess
import sys

def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

width, height = 640, 480
try:
    out = subprocess.check_output(['fbset', '-s'], text=True, stderr=subprocess.DEVNULL)
    for line in out.splitlines():
        if 'geometry' in line:
            parts = line.split()
            width, height = int(parts[1]), int(parts[2])
            break
except Exception:
    pass

bands = [
    rgb565(255,   0,   0),   # RED
    rgb565(  0, 255,   0),   # GREEN
    rgb565(  0,   0, 255),   # BLUE
    rgb565(255, 255, 255),   # WHITE
]

section = height // len(bands)

try:
    with open('/dev/fb0', 'wb') as fb:
        for y in range(height):
            idx = min(y // section, len(bands) - 1)
            fb.write(struct.pack('<H', bands[idx]) * width)
except PermissionError:
    print('Permission denied — try: sudo python3 test-display-color.py')
    sys.exit(1)

print('Test pattern written. You should see (top to bottom): RED  GREEN  BLUE  WHITE')

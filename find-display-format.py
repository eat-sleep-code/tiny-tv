#!/usr/bin/env python3
# Finds the correct pixel color encoding for the display by writing test
# patterns with different 16-bit encodings directly to /dev/fb0.
# No reboots needed — cycles in seconds.
#
# When correct you should see (top to bottom): RED  GREEN  BLUE  WHITE

import struct
import subprocess
import sys
import termios
import tty


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def swap_bytes(v):
    return ((v & 0xFF) << 8) | ((v >> 8) & 0xFF)

def rot_right(v, n):
    return ((v >> n) | (v << (16 - n))) & 0xFFFF

def rot_left(v, n):
    return ((v << n) | (v >> (16 - n))) & 0xFFFF


transforms = [
    # name,                             fn(r, g, b) -> 16-bit value
    ("RGB565 normal (baseline)",        lambda r,g,b: rgb565(r,g,b)),
    ("BGR565 — R and B swapped",        lambda r,g,b: rgb565(b,g,r)),
    ("RGB565 bytes swapped",            lambda r,g,b: swap_bytes(rgb565(r,g,b))),
    ("BGR565 bytes swapped",            lambda r,g,b: swap_bytes(rgb565(b,g,r))),
    ("RBG565 — G and B swapped",        lambda r,g,b: rgb565(r,b,g)),
    ("GRB565 — R and G swapped",        lambda r,g,b: rgb565(g,r,b)),
    ("GBR565",                          lambda r,g,b: rgb565(g,b,r)),
    ("BRG565",                          lambda r,g,b: rgb565(b,r,g)),
    ("RGB555",                          lambda r,g,b: ((r&0xF8)<<7)|((g&0xF8)<<2)|(b>>3)),
    ("BGR555",                          lambda r,g,b: ((b&0xF8)<<7)|((g&0xF8)<<2)|(r>>3)),
    ("RGB565 rotate right 1",           lambda r,g,b: rot_right(rgb565(r,g,b), 1)),
    ("RGB565 rotate right 2",           lambda r,g,b: rot_right(rgb565(r,g,b), 2)),
    ("RGB565 rotate right 3",           lambda r,g,b: rot_right(rgb565(r,g,b), 3)),
    ("RGB565 rotate right 4",           lambda r,g,b: rot_right(rgb565(r,g,b), 4)),
    ("RGB565 rotate right 5",           lambda r,g,b: rot_right(rgb565(r,g,b), 5)),
    ("RGB565 rotate left 1",            lambda r,g,b: rot_left(rgb565(r,g,b), 1)),
    ("RGB565 rotate left 2",            lambda r,g,b: rot_left(rgb565(r,g,b), 2)),
    ("RGB565 rotate left 3",            lambda r,g,b: rot_left(rgb565(r,g,b), 3)),
    ("RGB565 rotate left 4",            lambda r,g,b: rot_left(rgb565(r,g,b), 4)),
    ("RGB565 rotate left 5",            lambda r,g,b: rot_left(rgb565(r,g,b), 5)),
]


def get_dims():
    width, height = 640, 480
    try:
        out = subprocess.check_output(['fbset', '-s'], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if 'geometry' in line:
                parts = line.split()
                width, height = int(parts[1]), int(parts[2])
    except Exception:
        pass
    return width, height


def draw(fn, width, height):
    RED   = struct.pack('<H', fn(255,   0,   0))
    GREEN = struct.pack('<H', fn(  0, 255,   0))
    BLUE  = struct.pack('<H', fn(  0,   0, 255))
    WHITE = struct.pack('<H', fn(255, 255, 255))
    section = height // 4
    with open('/dev/fb0', 'wb') as fb:
        for y in range(height):
            if   y < section:     fb.write(RED   * width)
            elif y < section * 2: fb.write(GREEN * width)
            elif y < section * 3: fb.write(BLUE  * width)
            else:                 fb.write(WHITE * width)


def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main():
    try:
        width, height = get_dims()
        index = 0
        total = len(transforms)

        print('\nDisplay Format Finder — no reboots needed')
        print('Look at the display. Correct = top-to-bottom: RED  GREEN  BLUE  WHITE')
        print('[n] next   [p] previous   [y] correct!   [q] quit\n')

        while True:
            name, fn = transforms[index]
            print(f'\r  [{index+1:2}/{total}] {name:<45}', end='', flush=True)
            draw(fn, width, height)

            key = getch()
            if key in ('y', 'Y'):
                print(f'\n\nFound it! Transform: {name}')
                print('Report this result so the correct dpi_output_format or VLC chroma setting can be determined.')
                break
            elif key in ('n', 'N'):
                index = (index + 1) % total
            elif key in ('p', 'P'):
                index = (index - 1) % total
            elif key in ('q', 'Q', '\x03'):
                print('\nQuitting.')
                break

    except PermissionError:
        print('Permission denied — try: sudo python3 find-display-format.py')
        sys.exit(1)


if __name__ == '__main__':
    main()

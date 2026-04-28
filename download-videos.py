#!/usr/bin/env python3
# Downloads and optionally processes YouTube videos for use with Tiny TV.
# Usage: python download-videos.py urls.txt [options]
# Requires: pip install yt-dlp   and   ffmpeg in PATH

import argparse
import os
import shutil
import subprocess
import sys
import yt_dlp


def sanitize_filename(name):
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, '')
    return name.strip()


def process_video(filepath, max_height, remove_vertical_bars, remove_horizontal_bars, resize, quality=29):
    tmp = filepath + '.tmp.mp4'
    if remove_vertical_bars:
        print('  Removing vertical bars...')
        subprocess.call([
            'ffmpeg', '-loglevel', 'error', '-i', filepath,
            '-filter:v', f'crop=ih/3*4:ih,scale=-2:{max_height},setsar=1',
            '-c:v', 'libx264', '-crf', str(quality), '-preset', 'veryfast',
            '-c:a', 'copy', '-y', tmp
        ])
        os.replace(tmp, filepath)
    elif remove_horizontal_bars:
        print('  Removing horizontal bars...')
        subprocess.call([
            'ffmpeg', '-loglevel', 'error', '-i', filepath,
            '-filter:v', f'crop=iw:iw/16*9,scale=-2:{max_height},setsar=1',
            '-c:v', 'libx264', '-crf', str(quality), '-preset', 'veryfast',
            '-c:a', 'copy', '-y', tmp
        ])
        os.replace(tmp, filepath)
    elif resize:
        print('  Resizing...')
        subprocess.call([
            'ffmpeg', '-loglevel', 'error', '-i', filepath,
            '-filter:v', f'scale=-2:{max_height},setsar=1',
            '-c:v', 'libx264', '-crf', str(quality), '-preset', 'veryfast',
            '-c:a', 'copy', '-y', tmp
        ])
        os.replace(tmp, filepath)


def download(url, output_folder, max_height, remove_vertical_bars, remove_horizontal_bars, resize):
    os.makedirs(output_folder, exist_ok=True)

    download_height = 720
    if max_height >= 4320:
        download_height = 4320
    elif max_height >= 2160:
        download_height = 2160
    elif max_height >= 1080:
        download_height = 1080

    ydl_opts = {
        'outtmpl': os.path.join(output_folder, '%(id)s.%(ext)s'),
        'format': f'best[height<={download_height}]/best[height<={download_height * 2}]/best',
        'quiet': True,
        'no_warnings': True,
    }

    print('  Downloading...')
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            video_id = info.get('id')
            ext = info.get('ext', 'mp4')
            title = sanitize_filename(info.get('title', video_id))
    except Exception as e:
        print(f'  ERROR: {e}')
        return False

    src = os.path.join(output_folder, f'{video_id}.{ext}')
    dst = os.path.join(output_folder, f'{title}.mp4')

    if not os.path.exists(src):
        print(f'  ERROR: expected output file not found: {src}')
        return False

    if src != dst:
        if ext != 'mp4':
            subprocess.call([
                'ffmpeg', '-loglevel', 'error', '-i', src, '-c', 'copy', '-y', dst
            ])
            os.remove(src)
        else:
            os.rename(src, dst)

    process_video(dst, max_height, remove_vertical_bars, remove_horizontal_bars, resize)

    print(f'  Saved: {dst}')
    return True


def main():
    if not shutil.which('ffmpeg'):
        print('WARNING: ffmpeg not found in PATH — video processing will fail.\n')

    parser = argparse.ArgumentParser(description='Batch download YouTube videos for Tiny TV')
    parser.add_argument('urlfile', help='Text file with one YouTube URL per line (# lines are ignored)')
    parser.add_argument('--output', dest='output', default='videos', help='Output folder (default: videos)')
    parser.add_argument('--maximumVideoHeight', dest='maximumVideoHeight', type=int, default=480, help='Maximum video height in pixels (default: 480)')
    parser.add_argument('--removeVerticalBars', dest='removeVerticalBars', action='store_true', default=False, help='Crop pillarbox black bars')
    parser.add_argument('--removeHorizontalBars', dest='removeHorizontalBars', action='store_true', default=False, help='Crop letterbox black bars')
    parser.add_argument('--resize', dest='resize', action='store_true', default=False, help='Resize to maximum video height without cropping')
    args = parser.parse_args()

    if not os.path.exists(args.urlfile):
        print(f'ERROR: File not found: {args.urlfile}')
        sys.exit(1)

    with open(args.urlfile, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    if not urls:
        print('No URLs found in file.')
        sys.exit(0)

    print(f'Processing {len(urls)} URL(s) → {os.path.abspath(args.output)}\n')

    success = 0
    for i, url in enumerate(urls, 1):
        print(f'[{i}/{len(urls)}] {url}')
        if download(url, args.output, args.maximumVideoHeight, args.removeVerticalBars, args.removeHorizontalBars, args.resize):
            success += 1
        print()

    print(f'Done: {success}/{len(urls)} succeeded.')


if __name__ == '__main__':
    main()

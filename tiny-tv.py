from datetime import datetime
from backlight import BacklightControl
from functions import Echo, Console
from time import sleep
import argparse
import glob
import mpv
import os
import pidfile
import random
import shutil
import subprocess
import sys
import yt_dlp


version = '2026.04.25'

os.environ['TERM'] = 'xterm-256color'

console = Console()
echo = Echo()
backlight = BacklightControl()


# === Argument Handling ========================================================

def parse_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', '1', 'on'):
        return True
    elif v.lower() in ('no', 'false', '0', 'off'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected')

parser = argparse.ArgumentParser()
parser.add_argument(dest='input', help='Video file, YouTube URL, or "category"', type=str)
parser.add_argument('--saveAs', dest='saveAs', help='Filename to save YouTube download as', type=str)
parser.add_argument('--category', dest='category', help='Video category subfolder', type=str)
parser.add_argument('--maximumVideoHeight', dest='maximumVideoHeight', help='Maximum video height in pixels', type=int, default=480)
parser.add_argument('--removeVerticalBars', dest='removeVerticalBars', help='Remove vertical black bars (pillarbox)', action='store_true', default=False)
parser.add_argument('--removeHorizontalBars', dest='removeHorizontalBars', help='Remove horizontal black bars (letterbox)', action='store_true', default=False)
parser.add_argument('--resize', dest='resize', help='Resize without cropping', action='store_true', default=False)
parser.add_argument('--volume', dest='volume', help='Initial volume percent (0-100)', type=int, default=100)
parser.add_argument('--loop', dest='loop', help='Loop playback continuously (default: true)', type=parse_bool, default=True)
parser.add_argument('--shuffle', dest='shuffle', help='Shuffle category playback', action='store_true', default=False)
args = parser.parse_args()

input_path     = (args.input or '').strip()
pidFilePath    = '/home/pi/tiny-tv/tiny-tv.pid'
saveAs         = args.saveAs or 'youtube-id'
maximumVideoHeight  = args.maximumVideoHeight
category       = args.category or ''
videoFolder    = '/home/pi/videos/'
videoCategoryFolder = videoFolder + category + '/'
removeVerticalBars  = args.removeVerticalBars
removeHorizontalBars = args.removeHorizontalBars
resize         = args.resize
loop           = args.loop
shuffle        = args.shuffle
quality        = 29   # CRF: lower = higher quality, larger file

volume         = max(0, min(100, args.volume))
volumeGradiation = 5
maxVolume      = 100
minVolume      = 0

playCount      = 0
quit_requested = False


# === Player Setup =============================================================

player = mpv.MPV(
    vo='fbdev',
    fullscreen=True,
    ao='alsa',
    really_quiet=True,
    input_default_bindings=False,
    input_vo_keyboard=True,
)
player.volume = volume


@player.on_key_press('q')
def on_quit():
    global quit_requested, playCount
    quit_requested = True
    playCount = -10
    echo.on()
    player.command('stop')


@player.on_key_press('+')
def on_vol_up():
    global volume
    volume = min(volume + volumeGradiation, maxVolume)
    player.volume = volume
    console.info('Volume: ' + str(volume) + '%')


@player.on_key_press('-')
def on_vol_down():
    global volume
    volume = max(volume - volumeGradiation, minVolume)
    player.volume = volume
    console.info('Volume: ' + str(volume) + '%')


@player.on_key_press('SPACE')
def on_space():
    player.pause = not player.pause


@player.on_key_press('LEFT')
def on_restart():
    console.info('Restarting current video...')
    player.seek(0, 'absolute-percent')


@player.on_key_press('RIGHT')
def on_next():
    console.info('Skipping to next video...')
    player.command('stop')


# === Playback Functions =======================================================

def getVideoPath(inputPath):
    try:
        os.makedirs(inputPath, exist_ok=True)
    except OSError:
        console.error('Creation of the output folder ' + inputPath + ' failed!')
        echo.on()
        quit()
    else:
        return inputPath


def playVideo(videoFullPath):
    if 'SSH_CONNECTION' in os.environ:
        console.warn('Tiny TV launched from SSH. Video(s) will not be displayed.')
        return True
    try:
        console.info('Playing ' + videoFullPath)
        backlight.fadeOn()
        player.play(videoFullPath)
        player.wait_for_playback()
        backlight.fadeOff()
        return True
    except Exception as ex:
        console.error(str(ex))
        return False


# === Tiny TV ==================================================================

try:
    os.chdir('/home/pi')
    console.print('\n Tiny TV ' + version)
    console.print('----------------------------------------------------------------------')
    console.print('\n Press [q] to quit, [space] pause, [left/right] restart/skip, [+/-] volume. \n')

    with pidfile.PIDFile(pidFilePath):
        backlight.off()

        if input_path.find('.') == -1 and input_path.find(';') == -1 and input_path.lower() != 'category':
            input_path = input_path + '.mp4'
        video = input_path


        # --- YouTube Download -------------------------------------------------

        if 'youtube.com' in video.lower():
            console.info('Starting download of video...')
            downloadHeight = 720
            if maximumVideoHeight >= 4320:
                downloadHeight = 4320
            elif maximumVideoHeight >= 2160:
                downloadHeight = 2160
            elif maximumVideoHeight >= 1080:
                downloadHeight = 1080

            formatString = f'best[height<={downloadHeight}]/best[height<={downloadHeight*2}]/best'
            youtubeDownloadOptions = {
                'outtmpl': videoCategoryFolder + '%(id)s.%(ext)s',
                'format': formatString,
                'js_runtimes': {'quickjs': {}},
            }
            try:
                with yt_dlp.YoutubeDL(youtubeDownloadOptions) as ydl:
                    info = ydl.extract_info(video)
                    video = info.get('id', None) + '.' + info.get('ext', None)
            except Exception as ex:
                console.error('Download failed: ' + str(ex))
                echo.on()
                sys.exit(1)

            console.info('Setting file owner to current user...')
            try:
                shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
            except Exception as ex:
                console.error(str(ex))

            if saveAs.lower() != 'youtube-id':
                try:
                    os.rename(videoCategoryFolder + video, videoCategoryFolder + saveAs)
                    video = saveAs
                except Exception as ex:
                    console.error(str(ex))


        # --- Pillar Box / Letter Box Removal ----------------------------------

        if removeVerticalBars:
            console.info('Removing vertical black bars (this will take a while)...')
            src = videoCategoryFolder + video
            tmp = videoCategoryFolder + '~' + video
            subprocess.call([
                'ffmpeg', '-i', src,
                '-filter:v', f'crop=ih/3*4:ih,scale=-2:{maximumVideoHeight},setsar=1',
                '-c:v', 'libx264', '-crf', str(quality), '-preset', 'veryfast',
                '-c:a', 'copy', tmp
            ])
            os.replace(tmp, src)
            try:
                shutil.chown(src, user='pi', group='pi')
            except Exception as ex:
                console.error(str(ex))

        elif removeHorizontalBars:
            console.info('Removing horizontal black bars (this will take a while)...')
            src = videoCategoryFolder + video
            tmp = videoCategoryFolder + '~' + video
            subprocess.call([
                'ffmpeg', '-i', src,
                '-filter:v', f'crop=iw:iw/16*9,scale=-2:{maximumVideoHeight},setsar=1',
                '-c:v', 'libx264', '-crf', str(quality), '-preset', 'veryfast',
                '-c:a', 'copy', tmp
            ])
            os.replace(tmp, src)
            try:
                shutil.chown(src, user='pi', group='pi')
            except Exception as ex:
                console.error(str(ex))

        if resize and not removeVerticalBars and not removeHorizontalBars:
            console.info('Resizing video (this will take a while)...')
            src = videoCategoryFolder + video
            tmp = videoCategoryFolder + '~' + video
            subprocess.call([
                'ffmpeg', '-i', src,
                '-filter:v', f'scale=-2:{maximumVideoHeight},setsar=1',
                '-c:v', 'libx264', '-crf', str(quality), '-preset', 'veryfast',
                '-c:a', 'copy', tmp
            ])
            os.replace(tmp, src)
            try:
                shutil.chown(src, user='pi', group='pi')
            except Exception as ex:
                console.error(str(ex))


        # --- Playback ---------------------------------------------------------

        playCount = 0
        backlight.off()
        while playCount >= 0 and not quit_requested:
            playCount += 1
            console.info('Starting playback (' + str(playCount) + ') at ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ...')

            if video.lower() == 'category':
                videosToPlay = glob.glob(videoCategoryFolder + '**/*.mp4', recursive=True)
                if shuffle:
                    random.shuffle(videosToPlay)
                for videoFullPath in videosToPlay:
                    if quit_requested:
                        break
                    playVideo(videoFullPath)
            else:
                playVideo(videoCategoryFolder + str(video))

            if not loop:
                break
            elif not quit_requested:
                sleep(1.5)

        player.terminate()
        try:
            os.remove(pidFilePath)
        except OSError:
            pass
        backlight.on()
        sys.exit(0)

except pidfile.AlreadyRunningError:
    console.error('Another instance of Tiny TV is already running. Exiting...')
    echo.on()
    sleep(1)
    sys.exit(1)

except KeyboardInterrupt:
    player.terminate()
    backlight.on()
    echo.on()
    sys.exit(0)

from datetime import datetime
from backlight import BacklightControl
from functions import Echo, Console
from time import sleep
import argparse
import glob
import os
import pidfile
import random
import shutil
import subprocess
import sys
import termios
import threading
import tty
import vlc
import yt_dlp


version = '2026.04.26'

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
parser.add_argument('--hue', dest='hue', help='Hue adjustment (-180 to 180, default: 0)', type=int, default=0)
parser.add_argument('--saturation', dest='saturation', help='Saturation (0.0 = grayscale, 1.0 = normal, default: 1.0)', type=float, default=1.0)
args = parser.parse_args()

input_path          = (args.input or '').strip()
pidFilePath         = '/home/pi/tiny-tv/tiny-tv.pid'
saveAs              = args.saveAs or 'youtube-id'
maximumVideoHeight  = args.maximumVideoHeight
category            = args.category or ''
videoFolder         = '/home/pi/videos/'
videoCategoryFolder = videoFolder + category + '/'
removeVerticalBars  = args.removeVerticalBars
removeHorizontalBars = args.removeHorizontalBars
resize              = args.resize
loop                = args.loop
shuffle             = args.shuffle
hue                 = max(-180, min(180, args.hue))
saturation          = max(0.0, min(3.0, args.saturation))
quality             = 29   # CRF: lower = higher quality, larger file

volume              = max(0, min(100, args.volume))
volumeGradiation    = 5
maxVolume           = 100
minVolume           = 0

playCount           = 0
quit_requested      = False
isPaused            = False


# === Player Setup =============================================================

vlcOptions = '--vout=fb --aout=alsa --no-osd --intf=dummy --no-video-title-show --quiet'
if hue != 0 or saturation != 1.0:
    vlcOptions += f' --video-filter=adjust --hue={hue} --saturation={saturation}'
instance = vlc.Instance(vlcOptions)
player = instance.media_player_new()
player.audio_set_volume(volume)


# === Keyboard Listener ========================================================

def start_keyboard_listener():
    def _listen():
        global volume, quit_requested, isPaused, playCount
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while not quit_requested:
                ch = sys.stdin.read(1)
                if not ch:
                    break
                if ch in ('q', '\x03'):                         # q or Ctrl-C
                    quit_requested = True
                    playCount = -10
                    player.stop()
                    echo.on()
                elif ch == '+':
                    volume = min(volume + volumeGradiation, maxVolume)
                    player.audio_set_volume(volume)
                    console.info('Volume: ' + str(volume) + '%')
                elif ch == '-':
                    volume = max(volume - volumeGradiation, minVolume)
                    player.audio_set_volume(volume)
                    console.info('Volume: ' + str(volume) + '%')
                elif ch == ' ':
                    isPaused = not isPaused
                    player.set_pause(1 if isPaused else 0)
                    console.info('Paused' if isPaused else 'Resumed')
                elif ch == '\x1b':                              # escape sequence
                    seq = sys.stdin.read(2)
                    if seq == '[D':                             # left arrow — restart
                        console.info('Restarting current video...')
                        player.set_position(0.0)
                    elif seq == '[C':                           # right arrow — skip
                        console.info('Skipping to next video...')
                        player.stop()
        except Exception:
            pass
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                pass

    t = threading.Thread(target=_listen, daemon=True)
    t.start()
    return t


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
    global isPaused
    if 'SSH_CONNECTION' in os.environ:
        console.warn('Tiny TV launched from SSH. Video(s) will not be displayed.')
        return True
    try:
        console.info('Playing ' + videoFullPath)
        media = instance.media_new(videoFullPath)
        player.set_media(media)
        player.audio_set_volume(volume)
        isPaused = False
        backlight.fadeOn()
        player.play()
        sleep(0.5)
        while player.get_state() not in (vlc.State.Ended, vlc.State.Error, vlc.State.Stopped):
            if quit_requested:
                break
            sleep(0.25)
        backlight.fadeOff()
        player.stop()
        media.release()
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

        start_keyboard_listener()


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

        player.release()
        instance.release()
        try:
            os.remove(pidFilePath)
        except OSError:
            pass
        backlight.on()
        echo.on()
        sys.exit(0)

except pidfile.AlreadyRunningError:
    console.error('Another instance of Tiny TV is already running. Exiting...')
    echo.on()
    sleep(1)
    sys.exit(1)

except KeyboardInterrupt:
    player.release()
    instance.release()
    backlight.on()
    echo.on()
    sys.exit(0)

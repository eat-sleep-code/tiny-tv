from functions import Echo, Console
from backlight import BacklightControl
from datetime import datetime
from sshkeyboard import listen_keyboard, stop_listening
from time import sleep
import argparse
import glob
import os
import random
import signal
import shutil
import subprocess
import sys
import threading
import vlc
import yt_dlp


version = '2024.02.22'

os.environ['TERM'] = 'xterm-256color'

console = Console()
echo = Echo()
backlight = BacklightControl()

# === Argument Handling ========================================================

parser = argparse.ArgumentParser()
parser.add_argument(dest='input', help='Select the video to be played', type=str)
parser.add_argument('--saveAs', dest='saveAs', help='Enter the name you would like the file saved as', type=str) # USED IF DOWNLOADING FROM YOUTUBE ONLY
parser.add_argument('--category', dest='category', help='Select the category', type=str)
parser.add_argument('--maximumVideoHeight', dest='maximumVideoHeight', help='Set the maximum height (in pixels) for the video', type=int, default=480) 
parser.add_argument('--removeVerticalBars', dest='removeVerticalBars', help='Remove the vertical black bars from the input file (time-intensive)', type=bool, default=False)
parser.add_argument('--removeHorizontalBars', dest='removeHorizontalBars', help='Remove the horizontal black bars from the input file (time-intensive)', type=bool, default=False)
parser.add_argument('--resize', dest='resize', help='Resize but do not crop', type=bool, default=False)
parser.add_argument('--volume', dest='volume', help='Set the initial volume percent', type=int, default=100)
parser.add_argument('--loop', dest='loop', help='Set whether video plays continuously in a loop', type=bool, default=True)
parser.add_argument('--shuffle', dest='shuffle', help='Set whether category-based playback is shuffled', type=bool, default=False)
args = parser.parse_args()


input = args.input or ''

# ------------------------------------------------------------------------------

saveAs = args.saveAs or 'youtube-id'

# ------------------------------------------------------------------------------

maximumVideoHeight = args.maximumVideoHeight

# ------------------------------------------------------------------------------

category = args.category or ''
videoFolder = '/home/pi/videos/'
videoCategoryFolder = videoFolder + category + '/'

# ------------------------------------------------------------------------------

removeVerticalBars = args.removeVerticalBars 

# ------------------------------------------------------------------------------

removeHorizontalBars = args.removeHorizontalBars 

# ------------------------------------------------------------------------------

resize = args.resize 

# ------------------------------------------------------------------------------

loop = args.loop 

# ------------------------------------------------------------------------------

shuffle = args.shuffle

# ------------------------------------------------------------------------------

volume = args.volume
volumeGradiation = 5
maxVolume = 100
minVolume = 0
try:
	if volume > maxVolume:
		volume = maxVolume
	if volume < minVolume:
		volume = minVolume
except:
	volume = 50

# ------------------------------------------------------------------------------

quality = 29   # Lower number = higher quality but bigger file size

# ------------------------------------------------------------------------------

instance = vlc.Instance('--aout=alsa --no-osd --fullscreen --align=0 --width=640 --height=480 --verbose -1')
player = instance.media_player_new()

# ------------------------------------------------------------------------------
		
playCount = 0
isPlaying = False
isPaused = False


# === Keyboard Watcher ========================================================

def watchForKeyPress():
	listen_keyboard(on_press=handleKeyPress)
			
def handleKeyPress(key):
	global instance 
	global player
	global playCount
	global volume
	global minVolume
	global maxVolume
	global volumeGradiation
	global isPlaying
	global isPaused
	if key == '+' and volume < (maxVolume - volumeGradiation):
		volume = volume + volumeGradiation
		console.info('Volume:' + str(volume) + '%')
		player.audio_set_volume(volume)
	elif key == '-' and volume > (minVolume + volumeGradiation):
		volume = volume - volumeGradiation
		console.info('Volume:' + str(volume) + '%')
		player.audio_set_volume(volume)
	elif key == 'space' and isPaused == False:
		isPaused = True
		isPlaying = True
		console.info('Pausing playback...')
		player.set_pause(1)
	elif key == 'space' and isPaused == True:
		isPlaying = True
		isPaused = False
		console.info('Resuming playback...')
		player.set_pause(0)
	elif key == 'left':
		console.info('Restarting current video...')
		player.set_position(0)
	elif key == 'right':
		console.info('Playing next video in playlist...')  
		isPaused = False
		isPlaying = False
		player.stop() 
	elif key == 'q':
		isPaused = False
		isPlaying = False
		playCount = -10
		player.stop()
		echo.on()
		os.kill(os.getpid(), signal.SIGKILL)
		sys.exit(0)

# === Playback Functions ======================================================

def getVideoPath(inputPath):
	try:
		os.makedirs(inputPath, exist_ok = True)
	except OSError:
		print ('\n ERROR: Creation of the output folder ' + inputPath + ' failed!' )
		echo.on()
		quit()
	else:
		return inputPath
   

def playVideo(videoFullPath):
	global instance
	global player
	global isPlaying
	global isPaused
	global volume
	global maxVolume
	global minVolume
	try:
		player = instance.media_player_new()
		media = instance.media_new(videoFullPath)
		print('Playing' + videoFullPath)
		player.set_media(media)
		player.audio_set_volume(volume)
		backlight.fadeOn()
		player.play()
		sleep(5)
		
		keyWatcherThread = threading.Thread(target=watchForKeyPress)
		keyWatcherThread.start()

		isPlaying = True
		isPaused = False
		while player.is_playing() == True or isPaused == True:
			sleep(1)

		isPlaying = False
		stop_listening()
		backlight.fadeOff()
		return True
	except Exception as ex:
		print ('\n ERROR: ' + str(ex))
		return False


# === Tiny TV ==================================================================

try: 
	os.chdir('/home/pi')
	backlight.off()
	print('\n Tiny TV ' + version )
	print('\n ----------------------------------------------------------------------\n')
	print('\n Press [Ctrl]-C to exit. \n')
	
	input = input.strip()
	if input.find('.') == -1 and input.find(';') == -1 and input.lower() != 'category':
		input = input + '.mp4'
	video = input
	
	
	# --- YouTube Download -------------------------------------------------

	if video.lower().find('youtube.com') != -1:
		print(' Starting download of video... ')
		downloadHeight = 720
		if maximumVideoHeight >= 4320: # Future product
			downloadHeight = 4320
		elif maximumVideoHeight >= 2160: # Minimum Raspberry Pi 4B
			downloadHeight = 2160
		elif maximumVideoHeight >= 1080: # Minimum Raspberry Pi 3B+
			downloadHeight = 1080

		try:
			youtubeDownloadOptions = { 
				'outtmpl': videoCategoryFolder + '%(id)s.%(ext)s',
				'format': 'best[height=' + str(downloadHeight) + ']'
			}
			with yt_dlp.YoutubeDL(youtubeDownloadOptions) as youtubeDownload:
				info = youtubeDownload.extract_info(video)
				video = info.get('id', None) + '.' + info.get('ext', None)
		except Exception as ex:
			console.info(' Falling back to best quality video... ')
			youtubeDownloadOptions = { 
				'outtmpl': videoCategoryFolder + '%(id)s.%(ext)s',
				'format': 'best'
			}
			with yt_dlp.YoutubeDL(youtubeDownloadOptions) as youtubeDownload:
				info = youtubeDownload.extract_info(video)
				video = info.get('id', None) + '.' + info.get('ext', None)
			pass

		console.info(' Setting the owner of the file to current user...')
		try:
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		except:
			pass
		
		if saveAs.lower() != 'youtube-id':
			try:
				os.rename(videoCategoryFolder + video, videoCategoryFolder + saveAs)
				video = saveAs
			except Exception as ex:
				console.info(str(ex))
	

	# --- Pillar Box / Letter Box Removal ----------------------------------

	if removeVerticalBars == True:
		console.info(' Starting removal of vertical black bars (this will take a while)... ')
		subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=ih/3*4:ih,scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf ' + str(quality) + ' -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"' , shell=True)
		os.remove(videoCategoryFolder + video)
		os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
		try:
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		except:
			pass

	elif removeHorizontalBars == True:
		console.info(' Starting removal of horizontal black bars (this will take a while)... ')
		subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=iw:iw/16*9,scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf ' + str(quality) + ' -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"', shell=True)
		os.remove(videoCategoryFolder + video)
		os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
		try:
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		except:
			pass
		

	# --- Resize only ------------------------------------------------------

	if resize == True and removeVerticalBars == False and removeHorizontalBars == False:
		console.info(' Starting resize to maximum video height (this will take a while)... ')
		subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf ' + str(quality) + ' -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"' , shell=True)
		os.remove(videoCategoryFolder + video)
		os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
		try:
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		except:
			pass
		
	
	# --- Playback ---------------------------------------------------------

	playCount = 0
	backlight.off()
	while playCount >= 0:
		playCount += 1
		console.info('\n Starting playback (' + str(playCount) + ') at ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ...')
		
		if (video.lower() == 'category'):
			videosToPlay = glob.glob(videoCategoryFolder + '**/*.mp4', recursive = True)
			if shuffle == True:
				random.shuffle(videosToPlay)
			for videoFullPath in videosToPlay:
				videoPlayed = playVideo(videoFullPath)
		else:
			videoFullPath = videoCategoryFolder + str(video)
			videoPlayed = playVideo(videoFullPath)
		if loop == False:
			break
		else:
			sleep(5)
		
	backlight.on()
	sys.exit(0)


except KeyboardInterrupt:
	backlight.on()
	echo.on()
	sleep(1)
	sys.exit(0)

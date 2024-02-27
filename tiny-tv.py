from datetime import datetime
from backlight import BacklightControl
from functions import Echo, Console
from time import sleep
import argparse
import glob
import os
import pidfile
import random
import signal
import shutil
import subprocess
import sys
import vlc
import yt_dlp


version = '2024.02.26'

os.environ['TERM'] = 'xterm-256color'
##print(os.environ)

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
pidFilePath = '/home/pi/tiny-tv/tiny-tv.pid'

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
isPaused = False


# === Keyboard Watcher ========================================================

def handleKeyPress(key):
	global instance 
	global player
	global playCount
	global volume
	global minVolume
	global maxVolume
	global volumeGradiation
	global isPaused
	try:
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
			console.info('Pausing playback...')
			player.set_pause(1)
		elif key == 'space' and isPaused == True:
			isPaused = False
			console.info('Resuming playback...')
			player.set_pause(0)
		elif key == 'left':
			console.info('Restarting current video...')
			player.set_position(0)
		elif key == 'right':
			console.info('Playing next video in playlist...')  
			isPaused = False
			player.stop() 
		elif key == 'q':
			isPaused = False
			playCount = -10
			player.stop()
			echo.on()
			os.kill(os.getpid(), signal.SIGKILL)
			sys.exit(0)
	except: 
		pass

# === Playback Functions ======================================================

def getVideoPath(inputPath):
	try:
		os.makedirs(inputPath, exist_ok = True)
	except OSError:
		console.error('Creation of the output folder ' + inputPath + ' failed!' )
		echo.on()
		quit()
	else:
		return inputPath
   

def playVideo(videoFullPath):
	global instance
	global player
	global isPaused
	global volume

	try:
		player = instance.media_player_new()
		media = instance.media_new(videoFullPath)
		console.info('Playing' + videoFullPath)
		isPaused = False
		if "SSH_CONNECTION" in os.environ:
			console.warn('Tiny TV launched from an SSH session.  Video(s) will not be displayed.')
		else:
			player.set_media(media)
			player.audio_set_volume(volume)
			backlight.fadeOn()
			player.play()
			sleep(1.5)
			duration = player.get_length() / 1000
			sleep(duration)
			backlight.fadeOff()
		return True
	except Exception as ex:
		console.error(str(ex))
		return False


# === Tiny TV ==================================================================

try: 
	os.chdir('/home/pi')
	console.print('\n Tiny TV ' + version )
	console.print('----------------------------------------------------------------------')
	console.print('\n Press [Ctrl]-C to exit. \n')
	

	try:
		with pidfile.PIDFile(pidFilePath):
			backlight.off()
			input = input.strip()
			if input.find('.') == -1 and input.find(';') == -1 and input.lower() != 'category':
				input = input + '.mp4'
			video = input
			
			
			# --- YouTube Download -------------------------------------------------

			if video.lower().find('youtube.com') != -1:
				console.info(' Starting download of video... ')
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
				console.info('Starting playback (' + str(playCount) + ') at ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ...')
				
				if (video.lower() == 'category'):
					videosToPlay = glob.glob(videoCategoryFolder + '**/*.mp4', recursive = True)
					if shuffle == True:
						random.shuffle(videosToPlay)
					for videoFullPath in videosToPlay:
						playVideo(videoFullPath)
				else:
					videoFullPath = videoCategoryFolder + str(video)
					playVideo(videoFullPath)
				if loop == False:
					break
				else:
					sleep(1.5)

			os.remove(pidFilePath)
			backlight.on()
			sys.exit(0)

	except pidfile.AlreadyRunningError:
		console.error('Another instance of Tiny TV is already running.   Exiting...')
		echo.on()
		sleep(1)
		sys.exit(0)
	except Exception:
		pass
	

except KeyboardInterrupt:
	backlight.on()
	echo.on()
	sys.exit(0)

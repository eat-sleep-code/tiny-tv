from datetime import datetime
from sshkeyboard import listen_keyboard, stop_listening
from time import sleep
import argparse
import glob
import os
import random
import subprocess
import shutil
import sys
import threading
import vlc
import youtube_dl


version = '2021.11.22'

os.environ['TERM'] = 'xterm-256color'

# === Argument Handling ========================================================

parser = argparse.ArgumentParser()
parser.add_argument(dest='input', help='Select the video to be played', type=str)
parser.add_argument('--saveAs', dest='saveAs', help='Enter the name you would like the file saved as', type=str) # USED IF DOWNLOADING FROM YOUTUBE ONLY
parser.add_argument('--category', dest='category', help='Select the category', type=str)
parser.add_argument('--maximumVideoHeight', dest='maximumVideoHeight', help='Set the maximum height (in pixels) for the video', type=int) 
parser.add_argument('--removeVerticalBars', dest='removeVerticalBars', help='Remove the vertical black bars from the input file (time-intensive)')
parser.add_argument('--removeHorizontalBars', dest='removeHorizontalBars', help='Remove the horizontal black bars from the input file (time-intensive)')
parser.add_argument('--resize', dest='resize', help='Resize but do not crop')
parser.add_argument('--volume', dest='volume', help='Set the initial volume percent', type=int)
parser.add_argument('--loop', dest='loop', help='Set whether video plays continuously in a loop')
parser.add_argument('--shuffle', dest='shuffle', help='Set whether category-based playback is shuffled')
args = parser.parse_args()


input = args.input or ''

# ------------------------------------------------------------------------------

saveAs = args.saveAs or 'youtube-id'

# ------------------------------------------------------------------------------

maximumVideoHeight = args.maximumVideoHeight or 480
try:
	maximumVideoHeight = int(maximumVideoHeight)
except:
	maximumVideoHeight = 480

# ------------------------------------------------------------------------------

category = args.category or ''
videoFolder = '/home/pi/videos/'
videoCategoryFolder = videoFolder + category + '/'

# ------------------------------------------------------------------------------

removeVerticalBars = args.removeVerticalBars or False
if str(removeVerticalBars) == 'True':
	removeVerticalBars = True
else:
	removeVerticalBars = False

# ------------------------------------------------------------------------------

removeHorizontalBars = args.removeHorizontalBars or False
if str(removeHorizontalBars) == 'True':
	removeHorizontalBars = True
else:
	removeHorizontalBars = False

# ------------------------------------------------------------------------------

resize = args.resize or False
if str(resize) == 'True':
	resize = True
else:
	resize = False

# ------------------------------------------------------------------------------

loop = args.loop or True
if str(loop) == 'False':
	loop = False
else:
	loop = True

# ------------------------------------------------------------------------------

shuffle = args.shuffle or False
if str(shuffle) == 'True':
	shuffle = True
else:
	shuffle = False

# ------------------------------------------------------------------------------

volume = args.volume or 100
volumeGradiation = 5
maxVolume = 100
minVolume = 0
try:
	volume = int(volume)
	if volume > maxVolume:
		volume = maxVolume
	if volume < minVolume:
		volume = minVolume
except:
	volume = 50

# ------------------------------------------------------------------------------

quality = 29   # Lower number = higher quality but bigger file size

# ------------------------------------------------------------------------------

playCount = 0
isPlaying = False
isPaused = False

# === Echo Control =============================================================

def echoOff():
	subprocess.run(['stty', '-echo'], check=True)
def echoOn():
	subprocess.run(['stty', 'echo'], check=True)
def clear():
	print('Clearing...')
	#subprocess.call('clear' if os.name == 'posix' else 'cls')
clear()


# === Backlight Control ========================================================

def backlightOff():
	try:
		subprocess.call('sudo echo 1 | sudo tee /sys/class/backlight/rpi_backlight/bl_power', shell=True)
		clear()
	except:
		pass


def backlightOn():
	try:
		subprocess.call('sudo echo 0 | sudo tee /sys/class/backlight/rpi_backlight/bl_power', shell=True)
		clear()
	except:
		pass


# === Keyboard Watcher ========================================================

def watchForKeyPress():
	listen_keyboard(on_press=handleKeyPress)
			
def handleKeyPress(key):
	global volume
	global minVolume
	global maxVolume
	global volumeGradiation
	global isPaused
	if key == '+' and volume < (maxVolume - volumeGradiation):
		volume = volume + volumeGradiation
		print('Volume increased to:', volume)
	elif key == '-' and volume > (minVolume + volumeGradiation):
		volume = volume - volumeGradiation
		print('Volume decreased to:', volume)
	elif key == 'space' and isPaused == False:
		isPaused = True
		print('Pausing playback...')
	elif key == 'space' and isPaused == True:
		isPaused = False
		print('Resuming playback...')


# === Playback Functions ======================================================

def getVideoPath(inputPath):
	try:
		os.makedirs(inputPath, exist_ok = True)
	except OSError:
		print ('\n ERROR: Creation of the output folder ' + inputPath + ' failed!' )
		echoOn()
		quit()
	else:
		return inputPath


def playVideo(instance, player, videoFullPath):
	global isPlaying
	global isPaused
	global volume
	global maxVolume
	global minVolume
	try:
		media = instance.media_new(videoFullPath)
		print('Playing' + videoFullPath)
		player.set_media(media)
		player.audio_set_volume(volume)
		backlightOn()
		player.play()
		sleep(5)
		
		keyWatcherThread = threading.Thread(target=watchForKeyPress)
		keyWatcherThread.start()

		isPlaying = True
		isPaused = False
		while isPlaying == True or (isPlaying == False and isPaused == True):
			print('isPlaying', isPlaying, '', 'isPaused', isPaused)
			player.audio_set_volume(volume)
			if isPaused == True:
				isPlaying = bool(player.is_playing())
				player.set_pause(1)
				sleep(1)
			else:
				player.set_pause(0)
				sleep(1)
				isPlaying = bool(player.is_playing())
			

		isPlaying = False
		stop_listening()
		backlightOff()
		return True
	except Exception as ex:
		print ('\n ERROR: ' + str(ex))
		return False


# === Tiny TV ==================================================================

try: 
	os.chdir('/home/pi')
	backlightOff()
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
			with youtube_dl.YoutubeDL(youtubeDownloadOptions) as youtubeDownload:
				info = youtubeDownload.extract_info(video)
				video = info.get('id', None) + '.' + info.get('ext', None)
		except Exception as ex:
			print(' Falling back to best quality video... ')
			youtubeDownloadOptions = { 
				'outtmpl': videoCategoryFolder + '%(id)s.%(ext)s',
				'format': 'best'
			}
			with youtube_dl.YoutubeDL(youtubeDownloadOptions) as youtubeDownload:
				info = youtubeDownload.extract_info(video)
				video = info.get('id', None) + '.' + info.get('ext', None)
			pass

		print(' Setting the owner of the file to current user...')
		try:
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		except:
			pass
		
		if saveAs.lower() != 'youtube-id':
			try:
				os.rename(videoCategoryFolder + video, videoCategoryFolder + saveAs)
				video = saveAs
			except Exception as ex:
				print(str(ex))
	

	# --- Pillar Box / Letter Box Removal ----------------------------------

	if removeVerticalBars == True:
		print(' Starting removal of vertical black bars (this will take a while)... ')
		subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=ih/3*4:ih,scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf ' + str(quality) + ' -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"' , shell=True)
		os.remove(videoCategoryFolder + video)
		os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
		try:
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		except:
			pass

	elif removeHorizontalBars == True:
		print(' Starting removal of horizontal black bars (this will take a while)... ')
		subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=iw:iw/16*9,scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf ' + str(quality) + ' -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"', shell=True)
		os.remove(videoCategoryFolder + video)
		os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
		try:
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		except:
			pass
		

	# --- Resize only ------------------------------------------------------

	if resize == True and removeVerticalBars == False and removeHorizontalBars == False:
		print(' Starting resize to maximum video height (this will take a while)... ')
		subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf ' + str(quality) + ' -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"' , shell=True)
		os.remove(videoCategoryFolder + video)
		os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
		try:
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		except:
			pass
		
	
	# --- Playback ---------------------------------------------------------

	playCount = 0
	backlightOff()
	while playCount >= 0:
		playCount += 1
		print('\n Starting playback (' + str(playCount) + ') at ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ...')
		instance = vlc.Instance("--vout=dummy --aout=alsa --no-osd --fullscreen --align=0 --width=640 --height=480")
		player = instance.media_player_new()
		
		
		if (video.lower() == 'category'):
			videosToPlay = glob.glob(videoCategoryFolder + '**/*.mp4', recursive = True)
			if shuffle == True:
				random.shuffle(videosToPlay)
			for videoFullPath in videosToPlay:
				videoPlayed = playVideo(instance, player, videoFullPath)
		else:
			videoFullPath = videoCategoryFolder + str(video)
			videoPlayed = playVideo(instance, player, videoFullPath)
		if loop == False:
			break
		else:
			sleep(5)
		
	sys.exit(0)

except KeyboardInterrupt:
	backlightOff()
	echoOn()
	sys.exit(1)

else:
	sys.exit(0)

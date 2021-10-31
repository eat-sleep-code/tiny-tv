from datetime import datetime
from time import sleep
import argparse
import glob
import os
import subprocess
import shutil
import sys
import youtube_dl

version = '2021.10.30'

# === Argument Handling ========================================================

parser = argparse.ArgumentParser()
parser.add_argument(dest='input', help='Select the video to be played', type=str)
parser.add_argument('--saveAs', dest='saveAs', help='Enter the name you would like the file saved as', type=str) # USED IF DOWNLOADING FROM YOUTUBE ONLY
parser.add_argument('--category', dest='category', help='Select the category', type=str)
parser.add_argument('--maximumVideoHeight', dest='maximumVideoHeight', help='Set the maximum height (in pixels) for the video', type=int) 
parser.add_argument('--removeVerticalBars', dest='removeVerticalBars', help='Remove the vertical black bars from the input file (time-intensive)')
parser.add_argument('--removeHorizontalBars', dest='removeHorizontalBars', help='Remove the horizontal black bars from the input file (time-intensive)')
parser.add_argument('--resize', dest='resize', help='Resize but do not crop')
parser.add_argument('--volume', dest='volume', help='Set the initial volume in decibels (-60 to 6)', type=int)
parser.add_argument('--loop', dest='loop', help='Set whether video plays continuously in a loop')
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

volume = args.volume or -20
maxVolume = 6
minVolume = -60
# Convert decibels to millibels
try:
	volume = int(volume) * 100
	if volume > maxVolume * 100:
		volume = maxVolume * 100
	if volume < minVolume * 100:
		volume = minVolume * 100
except:
	volume = -2000

# ------------------------------------------------------------------------------

quality = 29   # Lower number = higher quality but bigger file size

# ------------------------------------------------------------------------------

playCount = 0

# === Echo Control =============================================================

def echoOff():
	subprocess.run(['stty', '-echo'], check=True)
def echoOn():
	subprocess.run(['stty', 'echo'], check=True)
def clear():
	subprocess.call('clear' if os.name == 'posix' else 'cls')
clear()

# === Backlight Control ========================================================

def backlightOff():
	try:
		subprocess.call('sudo echo 1 | sudo tee /sys/class/backlight/rpi_backlight/bl_power', shell=True)
		clear()
	except:
		print('\n WARNING: Could not turn backlight off.')
		pass

def backlightOn():
	try:
		subprocess.call('sudo echo 0 | sudo tee /sys/class/backlight/rpi_backlight/bl_power', shell=True)
		clear()
	except:
		print('\n WARNING: Could not turn backlight on.')
		pass


# === Functions ================================================================

def getVideoPath(inputPath):
	try:
		os.makedirs(inputPath, exist_ok = True)
	except OSError:
		print ('\n ERROR: Creation of the output folder ' + inputPath + ' failed!' )
		echoOn()
		quit()
	else:
		return inputPath


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
		shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
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
		shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		
	elif removeHorizontalBars == True:
		print(' Starting removal of horizontal black bars (this will take a while)... ')
		subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=iw:iw/16*9,scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf ' + str(quality) + ' -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"', shell=True)
		os.remove(videoCategoryFolder + video)
		os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
		shutil.chown(videoCategoryFolder + video, user='pi', group='pi')

	# --- Resize only ------------------------------------------------------

	if resize == True and removeVerticalBars == False and removeHorizontalBars == False:
		print(' Starting resize to maximum video height (this will take a while)... ')
		subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf ' + str(quality) + ' -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"' , shell=True)
		os.remove(videoCategoryFolder + video)
		os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
		shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
	
	# --- Playback ---------------------------------------------------------

	playCount = 0
	while playCount >= 0:
		playCount += 1
		print('\n Starting playback (' + str(playCount) + ') at ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ...')
		if (video.lower() == 'category'):
			for videoFullPath in glob.glob(videoCategoryFolder + '**/*.mp4', recursive = True):
				backlightOn()
				subprocess.call('omxplayer -o alsa --vol ' + str(volume) + ' "' + videoFullPath + '"', shell=True)
				backlightOff()
		else:
			videoFullPath = videoCategoryFolder + str(video)
			backlightOn()
			subprocess.call('omxplayer -o alsa --vol ' + str(volume) + ' "' + videoFullPath + '"', shell=True)
			backlightOff()
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

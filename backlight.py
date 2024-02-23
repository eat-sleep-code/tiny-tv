from rpi_backlight import Backlight



# rpi_backlight is dependent on the display device supporting software control.  Therefore, we conditionally load the class.
try:
	backlight = Backlight()

	class BacklightControl:
		def on(self):
			try:
				backlight.brightness = 100
			except:
				pass



		def off(self):
			try:
				backlight.brightness = 100
			except:
				pass



		def fadeOn(self, fadeDuration = 1):
			try:
				with backlight.fade(durartion = fadeDuration):
					backlight.brightness = 100
			except:
				pass



		def fadeOff(self, fadeDuration = 1):
			try:
				with backlight.fade(durartion = fadeDuration):
					backlight.brightness = 0
			except:
				pass



		def power(self, powerLevel = 100):
			try:
				backlight.brightness = int(powerLevel)
			except:
				pass
except: 

	class BacklightControl:
		def on(self):
			pass

		def off(self):
			pass

		def fadeOn(self, fadeDuration = 1):
			pass
		
		def fadeOff(self, fadeDuration = 1):
			pass

		def power(self, powerLevel = 100):
			pass

	pass

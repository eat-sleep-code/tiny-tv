# Tiny TV


---
## Getting Started

- Use [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md) to:
  - Set up your WiFi connection
- Connect your display to your Raspberry Pi and configure according to the manufacturer's instructions
- Ensure audio output is correctly configured.

## Installation

Installation of the program, as well as any software prerequisites, can be completed with the following two-line install script.

```
wget -q https://raw.githubusercontent.com/eat-sleep-code/tiny-tv/master/install-tiny-tv.sh -O ~/install-tiny-tv.sh
sudo chmod +x ~/install-tiny-tv.sh && ~/install-tiny-tv.sh
```

---

## Usage
```
tiny-tv <options>
```

### Options

+ _--input_ : Select the video to be played    *(required, can be a file name or a Youtube URL)*
+ _--saveAs_ : Enter the name you would like the file saved as     *(Used if downloading from YouTube only)*
+ _--maximumVideoHeight_ : Set the maximum height (in pixels) for downloaded videos     *(Used if downloading from YouTube only)*
+ _--category_ : Select the category     *(This will set the subfolder, for example `--category cartoons` will use the `/home/pi/videos/cartoons` folder)*
+ _--removeVerticalBars_ : Remove the vertical black bars (pillar box) from the input file (time-intensive)    *(True/False)*
+ _--removeHorizontalBars_ : Remove the horizontal black bars (letter box) from the input file (time-intensive)    *(True/False)*
+ _--volume_ : Set the initial volume *(default: 400  `[4db]`)*


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
tiny-tv <input> [options]
```

### Options

+ _--input_ : Select the video to be played    *(required, can be a file name or a Youtube URL)*
+ _--saveAs_ : Enter the name you would like the file saved as     *(Used if downloading from YouTube only)*
+ _--category_ : Select the category     *(This will set the subfolder, for example `--category cartoons` will use the `/home/pi/videos/cartoons` folder)*
+ _--maximumVideoHeight_ : Set the maximum height (in pixels) for downloaded videos     *(default: 480)*
+ _--removeVerticalBars_ : Remove the vertical black bars (pillar box) from the input file.  This time-intensive process will also resize the video to the maximum video height.   *(default: False)*
+ _--removeHorizontalBars_ : Remove the horizontal black bars (letter box) from the input file.  This time-intensive process will also resize the video to the maximum video height.    *(default: False)*
+ _--resize_ : Resize the video to the maximum video height.  This is a time-intensive process.
+ _--volume_ : Set the initial volume *(default: 400  `[4db]`)*

### Examples

#### To download, crop, and play a video from YouTube:

```
tiny-tv https://www.youtube.com/watch?v=h8NrKjJPAuw --saveAs 'Bugs Bunny.mp4' --category 'cartoons' --removeVerticalBars True 
```

The default video height is 480px.  This is an ideal resolution for a true Tiny TV.  If you are utilizing a more powerful Raspberry Pi and a higher resolution screen, you may alter the maximum video height.

```
tiny-tv https://www.youtube.com/watch?v=h8NrKjJPAuw --saveAs 'Bugs Bunny.mp4' --category 'cartoons' --maximumVideoHeight 1080
```

#### To play a music video from your Raspberry Pi at a volume of 6db:

```
tiny-tv 'Becky G - Mayores (featuring Bad Bunny).mp4' --category 'music' --volume 600
```

Alternatively, you can type the video subfolder instead of using the category argument:

```
tiny-tv 'music/Becky G - Mayores (featuring Bad Bunny).mp4' --volume 600
```

## Audio Settings

If you are using a USB audio device you may need to edit the `/usr/share/alsa/alsa.conf` file for audio output to work.

Set the following values:

`defaults.ctl.card 1`
`defaults.pcm.card 1`
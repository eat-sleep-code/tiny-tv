# This script will install the Tiny TV software and any required prerequisites.
cd ~
echo -e ''
echo -e '\033[32mTiny TV [Installation Script] \033[0m'
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e ''
echo -e '\033[93mUpdating package repositories... \033[0m'
sudo apt update


echo ''
echo -e '\033[93mInstalling prerequisites... \033[0m'
sudo apt install -y git python3 python3-pip vlc ffmpeg fonts-freefont-ttf screen pulseaudio-module-bluetooth


sudo echo ''
echo -e '\033[93mProvisioning Python virtual environment... \033[0m'
sudo mkdir -p /home/pi/tiny-tv-venv
sudo chmod +rw /home/pi/tiny-tv-venv
sudo python3 -m venv /home/pi/tiny-tv-venv
sudo chown -R $USER:$USER /home/pi/tiny-tv-venv


echo -e '\033[93mInstalling Python libraries... \033[0m'
sudo /home/pi/tiny-tv-venv/bin/pip3 install pynput python-vlc yt-dlp rpi_backlight --force
echo 'SUBSYSTEM=="backlight",RUN+="/bin/chmod 666 /sys/class/backlight/%k/brightness /sys/class/backlight/%k/bl_power"' | sudo tee -a /etc/udev/rules.d/backlight-permissions.rules

echo ''
echo -e '\033[93mProvisioning logs... \033[0m'
sudo mkdir -p /home/pi/logs
sudo chmod +rw /home/pi/logs
sudo sed -i '\|^tmpfs /home/pi/logs|d' /etc/fstab
sudo sed -i '$ a tmpfs /home/pi/logs tmpfs defaults,noatime,nosuid,size=16m 0 0' /etc/fstab
sudo mount -a
sudo chown -R $USER:$USER /home/pi/logs
sudo systemctl daemon-reload

echo ''
echo -e '\033[93mInstalling Tiny TV... \033[0m'
cd ~
sudo rm -Rf ~/tiny-tv
sudo git clone https://github.com/eat-sleep-code/tiny-tv
sudo chown -R $USER:$USER tiny-tv
cd tiny-tv
sudo chmod +x tiny-tv.py
sudo chmod +x backlight.py

echo ''
echo -e '\033[93mCreating Service... \033[0m'
sudo mv tiny-tv.service /etc/systemd/system/tiny-tv.service
sudo chown root:root /etc/systemd/system/tiny-tv.service
sudo chmod +x *.sh 
echo 'Please see the README file for more information on configuring the service.'

cd ~
echo ''
echo -e '\033[93mSetting up aliases... \033[0m'
sudo touch ~/.bash_aliases
sudo sed -i '/\b\(function tiny-tv\)\b/d' ~/.bash_aliases
sudo sed -i '/\b\(function backlight\)\b/d' ~/.bash_aliases
echo "# Tiny TV" | sudo tee -a ~/.bash_aliases > /dev/null
sudo sed -i '$ a function tiny-tv { /home/pi/tiny-tv-venv/bin/python3 ~/tiny-tv/tiny-tv.py "$@"; }' ~/.bash_aliases
sudo sed -i '$ a function tiny-tv-persist { screen /home/pi/tiny-tv-venv/bin/python3 ~/tiny-tv/tiny-tv.py "$@"; }' ~/.bash_aliases
sudo sed -i '$ a function tiny-tv-resume { screen -r; }' ~/.bash_aliases
sudo sed -i '$ a function tiny-tv-start { systemctl start tiny-tv; }' ~/.bash_aliases
sudo sed -i '$ a function tiny-tv-stop { systemctl stop tiny-tv; }' ~/.bash_aliases
sudo sed -i '$ a function tiny-tv-update { wget -q https://raw.githubusercontent.com/eat-sleep-code/tiny-tv/master/install-tiny-tv.sh -O ~/install-tiny-tv.sh && sudo chmod +x ~/install-tiny-tv.sh && ~/install-tiny-tv.sh; }' ~/.bash_aliases
echo -e 'You may use \e[1mtiny-tv <options>\e[0m to launch the program.'
echo ''
echo ''
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e '\033[32mInstallation completed. \033[0m'
echo ''
bash

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
sudo apt install -y git python3 python3-pip omxplayer ffmpeg fonts-freefont-ttf
sudo pip3 install keyboard youtube_dl 

echo ''
echo -e '\033[93mInstalling Tiny TV... \033[0m'
cd ~
sudo rm -Rf ~/tiny-tv
sudo git clone https://github.com/eat-sleep-code/tiny-tv
sudo chown -R $USER:$USER tiny-tv
cd tiny-tv
sudo chmod +x tiny-tv.py

cd ~
echo ''
echo -e '\033[93mSetting up aliases... \033[0m'
sudo touch ~/.bash_aliases
sudo sed -i '/\b\(function tiny-tv\)\b/d' ~/.bash_aliases
sudo sed -i '$ a function tiny-tv { sudo python3 ~/tiny-tv/tiny-tv.py "$@"; }' ~/.bash_aliases
echo -e 'You may use \e[1mtiny-tv <options>\e[0m to launch the program.'
echo ''
echo ''
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e '\033[32mInstallation completed. \033[0m'
echo ''
bash

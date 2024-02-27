#!/bin/bash 
# This script will set Tiny TV to autostart when a local bash session starts.

AUTOSTARTCOMMAND=tiny-tv 'category' --category 'cartoons' --shuffle True --volume 0


# ==============================================================================
cd ~
echo ''
echo -e '\033[93mSetting up autostart... \033[0m'
sudo touch ~/.profile
sudo sed -i '/\b\(tiny-tv\)\b/d' ~/.profile
sudo sed -i "\$a$AUTOSTARTCOMMAND" ~/.profile
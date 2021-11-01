# This script will install the service to start the Tiny TV when the Raspberry Pi is started.
cd ~
echo -e ''
echo -e '\033[32mTiny TV Service [Installation Script] \033[0m'
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e ''
echo -e '\033[93mEnabling Service... \033[0m'
sudo systemctl enable tiny-tv.service

echo ''
echo -e '\033[93mStarting Service... \033[0m'
sudo systemctl start tiny-tv.service

mkdir /media/pi/USBDrive
sudo chown -R pi:pi /media/pi/USBDrive
sudo mount /dev/sda1 /media/pi/USBDrive -t vfat -o rw,uid=1000,gid=1000
ln -s /media/pi/USBDrive ~/videos

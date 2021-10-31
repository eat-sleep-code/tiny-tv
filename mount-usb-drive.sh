cd ~
sudo mkdir -p /media/pi/USBDrive
sudo chown -R pi:pi /media/pi/USBDrive
sudo mount /dev/sda1 /media/pi/USBDrive -t vfat -o rw,uid=1000,gid=1000
ln -s /media/pi/USBDrive ~/videos
sudo cp /etc/fstab /etc/fstab.back
# Run: sudo nano /etc/fstab
# Add this line: /dev/sda1 /media/pi/USBDrive vfat defaults,auto,users,rw,nofail,umask=000 0 0
# Reboot

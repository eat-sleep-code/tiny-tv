# Copy the display config to the right location
sudo wget -O /boot/firmware/mzp280v02br.txt https://raw.githubusercontent.com/tianyoujian/MZDPI/master/mzp280v02br/mzp280v02br.txt

# Add the include to firmware config (only if not already there)
grep -q "mzp280v02br" /boot/firmware/config.txt || echo -e "\n[all]\ninclude mzp280v02br.txt" | sudo tee -a /boot/firmware/config.txt

# Disable KMS — it conflicts with firmware DPI output
sudo sed -i 's/^dtoverlay=vc4-kms-v3d/#dtoverlay=vc4-kms-v3d/' /boot/firmware/config.txt
sudo reboot

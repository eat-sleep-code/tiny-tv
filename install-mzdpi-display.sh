# Configures the iUniker/Geekworm 2.8" MZDPI display (hardware version B) on
# Raspberry Pi OS Trixie.

# --- Legacy DPI configuration -------------------------------------------------
sudo wget -O /boot/firmware/mzp280v02br.txt https://raw.githubusercontent.com/tianyoujian/MZDPI/master/mzp280v02br/mzp280v02br.txt

grep -q "mzp280v02br" /boot/firmware/config.txt || echo -e "\n[all]\ninclude mzp280v02br.txt" | sudo tee -a /boot/firmware/config.txt

# Disable KMS — conflicts with firmware DPI output on this display
sudo sed -i 's/^dtoverlay=vc4-kms-v3d/#dtoverlay=vc4-kms-v3d/' /boot/firmware/config.txt

# --- Block kernel panel/DRM drivers from grabbing the display -----------------
# The firmware auto-generates a /panel device-tree node when enable_dpi_lcd=1,
# which causes kernel panel drivers to attach mid-boot and reconfigure the
# display. Blacklist them and disable the node via overlay.
sudo tee /etc/modprobe.d/blacklist-mzdpi.conf > /dev/null << 'EOF'
blacklist panel_simple
blacklist drm
blacklist drm_panel_orientation_quirks
EOF

sudo systemctl mask modprobe@drm.service 2>/dev/null

sudo reboot

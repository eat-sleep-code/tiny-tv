# Configures the iUniker/Geekworm 2.8" MZDPI display (hardware version B) on
# Raspberry Pi OS Trixie.

# --- Legacy DPI configuration -------------------------------------------------
sudo tee /boot/firmware/mzp280v02br.txt > /dev/null << 'EOF'
gpio=0-9=a2
gpio=12-17=a2
gpio=20-25=a2
gpio=18=op,dh,pd
display_rotate=3
framebuffer_width=640
framebuffer_height=480
enable_dpi_lcd=1
display_default_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=0x07f003
hdmi_timings=480 0 41 20 60 640 0 5 10 10 0 0 0 60 0 32000000 3
EOF

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

#!/bin/bash
# Configures the MZDPI iUniker 2.8" display (hardware version B) for
# Raspberry Pi OS Bookworm / Trixie using the modern KMS DPI panel approach.
# This fixes the blue color cast caused by firmware-level DPI format changes.

FIRMWARE_CONFIG=/boot/firmware/config.txt

echo ''
echo -e '\033[32mMZDPI Display Setup \033[0m'
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo ''

# Remove legacy MZDPI configuration if present from a previous install
if grep -q "mzp280v02br" "$FIRMWARE_CONFIG" 2>/dev/null; then
    echo -e '\033[93mRemoving legacy MZDPI configuration... \033[0m'
    sudo sed -i '/^include mzp280v02br\.txt/d' "$FIRMWARE_CONFIG"
    sudo rm -f /boot/firmware/mzp280v02br.txt
fi

# Re-enable KMS if it was commented out by a previous legacy install
echo -e '\033[93mEnsuring KMS overlay is enabled... \033[0m'
sudo sed -i 's/^#\(dtoverlay=vc4-kms-v3d\)/\1/' "$FIRMWARE_CONFIG"

# Add KMS DPI panel configuration (only if not already present)
if ! grep -q "vc4-kms-dpi-panel" "$FIRMWARE_CONFIG" 2>/dev/null; then
    echo -e '\033[93mAdding KMS DPI panel configuration... \033[0m'
    sudo tee -a "$FIRMWARE_CONFIG" > /dev/null << 'EOF'

[all]
# MZDPI iUniker 2.8" display - hardware version B
gpio=18=op,dh,pd
gpio=0-8=a2
gpio=12-17=a2
gpio=20-24=a2
dtoverlay=vc4-kms-dpi-panel,mzp280,rotate=270
dtparam=spi=on
dtoverlay=ads7846,penirq=27,swapxy=1,xmin=200,xmax=3850,ymin=200,ymax=3850
EOF
fi

echo ''
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e '\033[32mDisplay configuration complete. \033[0m'
echo ''
sudo reboot

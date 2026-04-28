#!/bin/bash
# Brute-forces dpi_output_format values to find correct color mapping.
# Run via SSH. Script shows a test pattern on the display, you evaluate,
# press y (correct) or n (try next — reboots). Resumes after each reboot.
#
# Currently (blue tint): RED=purple  GREEN=cyan  BLUE=very-blue  WHITE=blue-grey
# When correct:          RED=red     GREEN=green  BLUE=blue       WHITE=white

SCRIPT_DIR=/home/pi/tiny-tv
STATE_FILE="$SCRIPT_DIR/.dpi-brute-state"
CANDIDATES_FILE="$SCRIPT_DIR/.dpi-candidates"
DPI_CONFIG=/boot/firmware/mzp280v02br.txt
WORKING_VALUE="0x07f003"

# --- Candidate list -----------------------------------------------------------
generate_candidates() {
    # Vary lower byte (bits 0-7) keeping the 0x07f000 GPIO enables intact.
    # Current working-but-tinted value is 0x07f003 = 0x07f000 + 0x03.
    for i in $(seq 0 127); do
        printf "0x%06x\n" $(( 0x07f000 + i ))
    done

    # Vary the GPIO enable mask (bits 8-18) with the known format code 0x03
    for upper in 0x07e000 0x07d000 0x07b000 0x077000 0x06f000 0x05f000 0x03f000 0x0ff000; do
        printf "0x%06x\n" $(( upper + 0x03 ))
    done

    # Bit 24 set — plausible RGB/BGR swap flag added in newer Pi firmware
    for i in $(seq 0 31); do
        printf "0x%08x\n" $(( 0x1000000 + 0x07f000 + i ))
    done
}

# ------------------------------------------------------------------------------

if [ ! -f "$DPI_CONFIG" ]; then
    echo "ERROR: $DPI_CONFIG not found. Is the MZDPI display installed?"
    exit 1
fi

if [ ! -f "$CANDIDATES_FILE" ]; then
    echo "Generating candidate list..."
    generate_candidates > "$CANDIDATES_FILE"
    echo "$(wc -l < "$CANDIDATES_FILE") candidates generated."
fi

TOTAL=$(wc -l < "$CANDIDATES_FILE")

INDEX=0
[ -f "$STATE_FILE" ] && INDEX=$(cat "$STATE_FILE")

if [ "$INDEX" -ge "$TOTAL" ]; then
    echo ""
    echo "All $TOTAL candidates exhausted. Restoring $WORKING_VALUE and rebooting..."
    sudo sed -i "s/^dpi_output_format=.*/dpi_output_format=$WORKING_VALUE/" "$DPI_CONFIG"
    rm -f "$STATE_FILE" "$CANDIDATES_FILE"
    sleep 1
    sudo reboot
    exit 0
fi

VALUE=$(sed -n "$((INDEX+1))p" "$CANDIDATES_FILE")

echo ""
echo "========================================"
echo " DPI Brute Force  —  $((INDEX+1)) / $TOTAL"
echo " Testing: dpi_output_format=$VALUE"
echo "========================================"
echo ""

sudo sed -i "s/^dpi_output_format=.*/dpi_output_format=$VALUE/" "$DPI_CONFIG"
sudo python3 "$SCRIPT_DIR/test-display-color.py"

echo ""
echo " Currently (blue tint): RED=purple  GREEN=cyan  BLUE=very-blue  WHITE=blue-grey"
echo " When correct:          RED=red     GREEN=green  BLUE=blue       WHITE=white"
echo ""
echo " [y] correct!    [n] next (reboots)    [q] quit & restore $WORKING_VALUE"
echo ""
read -n 1 -s key
echo ""

case "$key" in
    y|Y)
        echo "SUCCESS: dpi_output_format=$VALUE"
        rm -f "$STATE_FILE" "$CANDIDATES_FILE"
        echo "Done. Reboot to confirm."
        ;;
    n|N)
        echo $((INDEX + 1)) > "$STATE_FILE"
        echo "Moving to next candidate after reboot..."
        sleep 1
        sudo reboot
        ;;
    q|Q)
        echo "Stopped at index $INDEX."
        sudo sed -i "s/^dpi_output_format=.*/dpi_output_format=$WORKING_VALUE/" "$DPI_CONFIG"
        echo "Restored $WORKING_VALUE. Reboot to return to normal."
        ;;
    *)
        echo "Unknown key — not advancing. Run the script again."
        sudo sed -i "s/^dpi_output_format=.*/dpi_output_format=$WORKING_VALUE/" "$DPI_CONFIG"
        ;;
esac

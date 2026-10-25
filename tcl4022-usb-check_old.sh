#!/usr/bin/env bash
# TCL 4022 USB diagnostics for Arch Linux
# Usage: bash tcl4022-usb-check.sh
set -u

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${PWD}/tcl4022-usb-report-${STAMP}"
mkdir -p "$OUT"
REPORT="$OUT/report.txt"
exec > >(tee "$REPORT") 2>&1

section() { printf '\n\n========== %s ==========\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "TCL 4022 USB diagnostics"
echo "Date: $(date --iso-8601=seconds)"
echo "Report folder: $OUT"
echo "This script only reads device/system information; it does not modify the phone."

section "Linux system"
uname -a
printf '\nDistribution:\n'
if [[ -r /etc/os-release ]]; then cat /etc/os-release; fi
printf '\nUSB-related tools:\n'
for cmd in lsusb udevadm journalctl dmesg lsblk findmnt gio mtp-detect jmtpfs simple-mtpfs adb fastboot; do
    if have "$cmd"; then printf '%-15s %s\n' "$cmd" "$(command -v "$cmd")"; else printf '%-15s %s\n' "$cmd" "not installed"; fi
done

section "USB devices (lsusb)"
if have lsusb; then
    lsusb
    echo
    echo "USB device tree:"
    lsusb -t
else
    echo "lsusb missing. Install with: sudo pacman -S usbutils"
fi

section "Current USB device descriptors"
if have lsusb; then
    if [[ -n "${SUDO_USER:-}" ]]; then
        lsusb -v 2>&1 | head -n 500
    elif sudo -n true 2>/dev/null; then
        sudo lsusb -v 2>&1 | head -n 500
    else
        echo "Detailed descriptors may require privileges. Run this command manually if needed:"
        echo "sudo lsusb -v"
        lsusb -v 2>&1 | head -n 180
    fi
fi

section "Recent kernel messages (USB)"
if have journalctl; then
    journalctl -k -b --no-pager 2>/dev/null | grep -Ei 'usb|mtp|mass storage|ttyUSB|ttyACM|cdc_acm|media transfer' | tail -n 160 || true
else
    dmesg 2>&1 | grep -Ei 'usb|mtp|mass storage|ttyUSB|ttyACM|cdc_acm|media transfer' | tail -n 160 || true
fi

section "USB-related device nodes"
for pattern in /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/* /dev/disk/by-id/usb-*; do
    compgen -G "$pattern" 2>/dev/null || true
done
echo
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id /dev/disk/by-id/usb-* 2>&1 || true

section "Block devices and mounts"
lsblk -o NAME,TRAN,TYPE,FSTYPE,LABEL,UUID,SIZE,MOUNTPOINTS 2>&1 || true
echo
findmnt -rn -o SOURCE,TARGET,FSTYPE,OPTIONS 2>&1 | grep -Ei 'usb|mtp|gvfs|run/user|media|sd[a-z]' || true

section "Udev information for USB devices"
if have udevadm; then
    for node in /sys/bus/usb/devices/*; do
        [[ -r "$node/idVendor" && -r "$node/idProduct" ]] || continue
        bus="$(basename "$node")"
        vid="$(cat "$node/idVendor" 2>/dev/null || true)"
        pid="$(cat "$node/idProduct" 2>/dev/null || true)"
        echo
        echo "--- $bus  VID:PID=$vid:$pid ---"
        udevadm info --query=property --path="$node" 2>/dev/null | grep -E '^(DEVTYPE|PRODUCT|TYPE|BUSNUM|DEVNUM|ID_VENDOR|ID_MODEL|ID_SERIAL|ID_USB_DRIVER|ID_USB_INTERFACES)=' || true
    done
fi

section "MTP checks"
if have mtp-detect; then
    echo "Running mtp-detect (may take a few seconds):"
    timeout 15s mtp-detect 2>&1 || true
else
    echo "mtp-detect is not installed. Optional package: libmtp (sudo pacman -S libmtp)"
fi
if have gio; then
    echo
    echo "GVFS-visible devices:"
    gio mount -l 2>&1 || true
fi

section "Android/debug interface checks"
if have adb; then
    adb devices -l 2>&1
else
    echo "adb not installed; this is only a check, not a recommendation to use Android tools on this phone."
fi
if have fastboot; then
    fastboot devices 2>&1
else
    echo "fastboot not installed."
fi

section "Interpretation hints"
cat <<'HINTS'
- A new lsusb VID:PID line and a matching kernel USB log mean the computer detects a USB device.
- "Mass Storage" or a new block device may indicate an accessible memory card/storage.
- MTP detection means file transfer may be possible; it does NOT mean app installation is supported.
- No ADB/fastboot result is expected on many feature phones and does not prove the phone is defective.
- USB alone usually cannot reveal the screen resolution, physical keypad scan codes, or whether third-party apps can run.
- To compare before/after, run this once with the phone unplugged and again with it plugged in and powered on.
HINTS

section "Report complete"
echo "Saved report: $REPORT"
echo "Folder: $OUT"

from pathlib import Path
script = r'''#!/usr/bin/env bash
# TCL 4022 USB diagnostics + dependency setup for Arch Linux
# Usage: ./tcl4022-usb-check.sh
# Installs the diagnostic tools with pacman (sudo required), then gathers reports.
set -Eeuo pipefail

if [[ ! -r /etc/arch-release ]]; then
    echo "HATA: Bu script Arch Linux için hazırlandı (/etc/arch-release bulunamadı)." >&2
    exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
    echo "HATA: sudo bulunamadı. Önce sudo kurup kullanıcıya yetki vermelisin." >&2
    exit 1
fi

echo "TCL 4022 USB tanılama aracı"
echo "Gerekli paketler kurulacak; sudo parolanı girmen istenecek."
echo "Kurulacak paketler: usbutils, libmtp, gvfs-mtp, android-tools"
echo "Not: Bunlar tanılama araçlarıdır; telefonun desteklemediği özellikleri eklemez."
sudo -v

# Install all tools in one pacman transaction.
sudo pacman -S --needed --noconfirm usbutils libmtp gvfs-mtp android-tools

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${PWD}/tcl4022-usb-report-${STAMP}"
mkdir -p "$OUT"
REPORT="$OUT/report.txt"
exec > >(tee "$REPORT") 2>&1

section() { printf '\n\n========== %s ==========\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

section "Run information"
echo "Date: $(date --iso-8601=seconds)"
echo "Kernel: $(uname -a)"
echo "Report folder: $OUT"
echo "This script installs diagnostic tools and reads system/device information."
echo "It does not write to the phone or attempt to unlock/flash it."

section "Installed tools"
for cmd in lsusb udevadm journalctl lsblk findmnt gio mtp-detect adb fastboot; do
    if have "$cmd"; then printf '%-15s %s\n' "$cmd" "$(command -v "$cmd")"; else printf '%-15s %s\n' "$cmd" "not found"; fi
done

section "USB devices (lsusb)"
lsusb
echo
lsusb -t

section "Detailed USB descriptors"
# Some devices restrict descriptors without elevated privileges.
sudo lsusb -v 2>&1 | head -n 700 || true

section "Recent kernel messages related to USB"
sudo journalctl -k -b --no-pager 2>/dev/null \
  | grep -Ei 'usb|mtp|mass storage|ttyUSB|ttyACM|cdc_acm|media transfer' \
  | tail -n 220 || true

section "USB device properties"
for node in /sys/bus/usb/devices/*; do
    [[ -r "$node/idVendor" && -r "$node/idProduct" ]] || continue
    bus="$(basename "$node")"
    vid="$(cat "$node/idVendor" 2>/dev/null || true)"
    pid="$(cat "$node/idProduct" 2>/dev/null || true)"
    echo
    echo "--- $bus VID:PID=$vid:$pid ---"
    sudo udevadm info --query=property --path="$node" 2>/dev/null \
      | grep -E '^(DEVTYPE|PRODUCT|TYPE|BUSNUM|DEVNUM|ID_VENDOR|ID_MODEL|ID_SERIAL|ID_USB_DRIVER|ID_USB_INTERFACES)=' || true
done

section "Serial and USB storage nodes"
for pattern in /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/* /dev/disk/by-id/usb-*; do
    compgen -G "$pattern" 2>/dev/null || true
done
echo
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id /dev/disk/by-id/usb-* 2>&1 || true

section "Block devices and mounts"
lsblk -o NAME,TRAN,TYPE,FSTYPE,LABEL,UUID,SIZE,MOUNTPOINTS 2>&1 || true
echo
findmnt -rn -o SOURCE,TARGET,FSTYPE,OPTIONS 2>&1 | grep -Ei 'usb|mtp|gvfs|run/user|media|sd[a-z]' || true

section "MTP detection"
timeout 20s mtp-detect 2>&1 || true
echo
gio mount -l 2>&1 || true

section "Android/debug interface checks"
adb devices -l 2>&1 || true
fastboot devices 2>&1 || true

section "Summary and limits"
cat <<'HINTS'
- Compare this report with one taken while the phone is unplugged to identify new devices.
- VID:PID and kernel logs can identify the USB interface and sometimes the chipset/vendor.
- MTP or USB mass storage can indicate file-transfer access, not application installation support.
- Empty ADB/Fastboot output is common for feature phones and does not mean the phone is broken.
- USB alone cannot reliably reveal physical keypad behavior, screen resolution, or whether third-party apps can run.
- The script does not format, flash, unlock, or modify the phone.
HINTS

section "Complete"
echo "Report saved to: $REPORT"
echo "Report folder: $OUT"
'''
p = Path("/mnt/data/tcl4022-usb-check.sh")
p.write_text(script, encoding="utf-8")
p.chmod(0o755)
print(f"Updated: {p}")

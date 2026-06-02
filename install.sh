#!/bin/bash
set -e

KLIPPER_PATH="${HOME}/klipper"
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

while getopts "k:" arg; do
    case $arg in
        k) KLIPPER_PATH=$OPTARG;;
    esac
done

if [ "$EUID" -eq 0 ]; then
    echo "This script must not run as root"
    exit 1
fi

echo "Linking extension to Klipper..."
ln -sf "${SRCDIR}/network_status.py" "${KLIPPER_PATH}/klippy/extras/network_status.py"
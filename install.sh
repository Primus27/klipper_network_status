#!/bin/bash
set -e

KLIPPER_PATH="${HOME}/klipper"
KLIPPY_ENV="${HOME}/klippy-env"
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$EUID" -eq 0 ]; then
    echo "This script must not run as root"
    exit 1
fi

while getopts "k:e:" arg; do
    case $arg in
        k) KLIPPER_PATH=$OPTARG;;
        e) KLIPPY_ENV=$OPTARG;;
    esac
done

if [ ! -d "${KLIPPER_PATH}/klippy/extras" ]; then
    echo "Klipper extras directory not found at ${KLIPPER_PATH}/klippy/extras"
    echo "Use -k to specify your Klipper path"
    exit 1
fi

if [ ! -f "${KLIPPY_ENV}/bin/pip" ]; then
    echo "Klipper virtualenv not found at ${KLIPPY_ENV}"
    echo "Use -e to specify your Klipper virtualenv path"
    exit 1
fi

echo "Installing dependencies..."
"${KLIPPY_ENV}/bin/pip" install -r "${SRCDIR}/requirements.txt"

echo "Linking extension to Klipper..."
ln -sf "${SRCDIR}/network_status.py" "${KLIPPER_PATH}/klippy/extras/network_status.py"

echo "Done. Happy printing!"
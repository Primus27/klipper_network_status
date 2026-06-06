# Klipper Network Status Plugin

Allow gcode macros and display menus to access system network info: IP addresses, Wi-Fi SSID, mDNS hostname, and connection status.

## Installation

Clone the repo into your home directory and run the install script:

> Note: The install script accepts two optional flags:
> - `-k <klipper_path>` - path to your Klipper directory (default: `~/klipper`)
> - `-e <venv_path>` - path to your Klipper virtualenv (default: `~/klippy-env`)
>
> If you don't know what this means, ignore this hint.

```sh
cd ~
git clone https://github.com/Primus27/klipper_network_status.git
chmod +x klipper_network_status/install.sh
bash klipper_network_status/install.sh
```

Then add the following to your `moonraker.conf` to enable automatic updates:

```ini
[update_manager klipper_network_status]
type: git_repo
path: ~/klipper_network_status
origin: https://github.com/Primus27/klipper_network_status.git
virtualenv: ~/klippy-env
requirements: requirements.txt
managed_services: klipper
```

Finally, add the following to your `printer.cfg` to enable the plugin:

```ini
[network_status]
```

## Configuration

An optional `interval` parameter controls how often network info is refreshed (in seconds). The default is 60, minimum is 10:

```ini
[network_status]
interval: 30
```

## Usage

Network details are exposed as printer objects and can be referenced in macros
and display menus as `printer.network_status.<field>`.

### Top-level fields

| Field | Description | Example |
|-------|-------------|---------|
| `status` | Connection status | `Connected` |
| `mdns` | mDNS hostname | `printer.local` |
| `interfaces` | Per-interface details, keyed by interface name | — |

### Per-interface fields

Accessed as `printer.network_status.interfaces.<name>.<field>`, where `<name>` is the interface name (e.g. `eth0`, `wlan0`).

| Field | Description | Example |
|-------|-------------|---------|
| `ip` | IP address (IPv4 if available, else IPv6) | `192.168.1.10` |
| `ipv4` | IPv4 address | `192.168.1.10` |
| `ipv6` | IPv6 address | `fe80::1` |
| `mac` | MAC address | `aa:bb:cc:dd:ee:ff` |
| `ssid` | Wi-Fi network name (Wi-Fi interfaces only) | `MyNetwork` |

Fields return `None` if the information is unavailable.

### Example: display menu

Add a Network submenu to your display config. Replace `eth0` and `wlan0` with your actual interface names:

```ini
[menu __main __network]
type: list
name: Network

[menu __main __network _status]
type: command
name: Status: {printer.network_status.status}

[menu __main __network _mdns]
type: command
name: mDNS: {printer.network_status.mdns}

[menu __main __network _ethip]
type: command
name: Eth IP: {printer.network_status.interfaces.eth0.ip}

[menu __main __network _wifissid]
type: command
name: Wifi SSID: {printer.network_status.interfaces.wlan0.ssid}

[menu __main __network _wifiip]
type: command
name: Wifi IP: {printer.network_status.interfaces.wlan0.ip}
```
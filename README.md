# Klipper Network Status Plugin

Allow gcode macros and display menus to access system network info: IP addresses, Wi-Fi SSID, mDNS hostname, and connection status.

## Installation

Clone the repo into your home directory and run the install script:

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
virtualenv: ~/.klippy-env
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
and display menus as `printer.network_status.<field>`:

| Field | Description | Example |
|-------|-------------|---------|
| `status` | Connection status | `Connected` |
| `ethip` | Ethernet IP address (ipv4 w/ ipv6 fallback) | `192.168.1.10` |
| `wifiip` | Wi-Fi IP address (ipv4 w/ ipv6 fallback) | `192.168.1.11` |
| `wifissid` | Wi-Fi network name | `MyNetwork` |
| `mdns` | mDNS hostname | `printer.local` |

Fields return `N/A` if the information is unavailable.

### Example: display menu

Add a Network submenu to your display config:

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
name: Eth IP: {printer.network_status.ethip}

[menu __main __network _wifissid]
type: command
name: Wifi SSID: {printer.network_status.wifissid}

[menu __main __network _wifiip]
type: command
name: Wifi IP: {printer.network_status.wifiip}
```
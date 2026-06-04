import os
import logging
from dataclasses import dataclass, fields, field
import socket
import threading
from typing import Any
import psutil


def get_ssid(iface: str) -> str | None:
    """
    Get SSID from the interface name via the wpa_supplicant socket

    :param iface: Interface name
    :return: SSID or None (if interface does not exist or has no SSID)
    """
    sock_path = f"/var/run/wpa_supplicant/{iface}"
    if not os.path.exists(sock_path):
        return None

    client = f"/tmp/wpa_ctrl_{os.getpid()}"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    s.bind(client)

    try:
        s.connect(sock_path)
        s.send(b"STATUS")
        data = s.recv(4096).decode()
        for line in data.splitlines():
            if line.startswith("ssid="):
                return line[5:]  # remove `ssid=` prefix

    finally:
        s.close()
        try:
            os.unlink(client)
        except OSError:  # Might not exist if connection not created
            pass

    return None


@dataclass
class SerializableMixin:
    def _serialize(self, value):
        if isinstance(value, SerializableMixin):
            return value.to_dict()
        elif isinstance(value, dict):
            return {k: self._serialize(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._serialize(v) for v in value]
        return value

    def to_dict(self):
        result = {f.name: self._serialize(getattr(self, f.name)) for f in fields(self)}
        result.update(
            {
                name: getattr(self, name)
                for name, val in vars(type(self)).items()
                if isinstance(val, property)
            }
        )
        return result


@dataclass
class InterfaceDetails(SerializableMixin):
    ipv4: str | None = None
    ipv6: str | None = None
    mac: str | None = None
    ssid: str | None = None

    @property
    def ip(self):
        return self.ipv4 or self.ipv6

    @classmethod
    def from_snicaddrs(cls, iface: str, snicaddrs: list):
        """
        Create an InterfaceDetails instance from the psutil net_if_addrs interface output

        :param iface: Interface name
        :param snicaddrs: Psutil's SNICADDR output
        :return: InterfaceDetails instance
        """
        details = cls()

        if (ssid := get_ssid(iface)) is not None:
            details.ssid = ssid

        for addr in snicaddrs:
            if addr.family == socket.AF_INET:
                details.ipv4 = addr.address
            elif addr.family == socket.AF_INET6:
                details.ipv6 = addr.address
            elif addr.family == psutil.AF_LINK:
                details.mac = addr.address

        return details


@dataclass
class NetworkDetails(SerializableMixin):
    mdns: str | None = field(default=None)
    interfaces: dict[str, InterfaceDetails] = field(default_factory=dict)

    @property
    def status(self):
        for interface in self.interfaces.values():
            if interface.ip is not None:
                return "Connected"
        return "Disconnected"


class network_status:
    def __init__(self, config):
        """
        Init

        :param config: config object from Klipper
        """
        self.printer = config.get_printer()
        self.interval_secs = config.getint("interval", 60, minval=10)
        self.details: dict[str, Any] = NetworkDetails().to_dict()

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.refresh_thread = None
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.printer.register_event_handler(
            "klippy:disconnect", self._handle_disconnect
        )

    def _handle_ready(self):
        """
        Refresh network info on a background thread so the blocking subprocess calls never stall Klipper's main thread
        """
        self.stop_event.clear()
        self.refresh_thread = threading.Thread(
            target=self._refresh_loop, name="network_status"
        )
        self.refresh_thread.daemon = True
        self.refresh_thread.start()

    def _handle_disconnect(self):
        """
        Set stop event in case of disconnection to exit refresh loop early
        """
        self.stop_event.set()

    def _refresh_loop(self):
        """
        Update status loop caller
        """
        while not self.stop_event.is_set():
            self._refresh()
            # Wait returns early if stop_event is set, so shutdown is prompt.
            self.stop_event.wait(self.interval_secs)

    def _refresh(self):
        """
        Method to update network details
        """
        logging.debug("network_status refresh")
        details = NetworkDetails()

        network_addrs = psutil.net_if_addrs()
        _ = network_addrs.pop("lo", None)

        details.interfaces = {
            k: InterfaceDetails.from_snicaddrs(k, v) for k, v in network_addrs.items()
        }

        try:
            details.mdns = socket.gethostname() + ".local"
        except Exception:
            pass

        with self.lock:
            self.details = details.to_dict()  # Pre-serialised

    def get_status(self, eventtime) -> dict:
        """
        Klipper call method

        :return: Network details
        """
        with self.lock:
            return self.details


def load_config(config):
    return network_status(config)

import os
import logging
from dataclasses import dataclass, asdict
from typing import Literal
import socket
import threading
import psutil
from psutil._ntuples import snicaddr


@dataclass
class InterfaceDetails:
    ipv4: str | None = None
    ipv6: str | None = None
    mac: str | None = None

    @classmethod
    def from_snicaddrs(cls, snicaddrs: list[snicaddr]):
        """
        Create an InterfaceDetails instance from the psutil net_if_addrs interface output

        :param snicaddrs: Psutil's SNICADDR output
        :return: InterfaceDetails instance
        """
        details = cls()
        for addr in snicaddrs:
            if addr.family == socket.AF_INET:
                details.ipv4 = addr.address
            elif addr.family == socket.AF_INET6:
                details.ipv6 = addr.address
            elif addr.family == psutil.AF_LINK:
                details.mac = addr.address
        return details

@dataclass
class NetworkDetails:
    status: Literal["Connected", "Disconnected", "N/A"] = "N/A"
    ethip: str = "N/A"
    wifiip: str = "N/A"
    wifissid: str = "N/A"
    mdns: str = "N/A"


class network_status:
    def __init__(self, config):
        """
        Init

        :param config: config object from Klipper
        """
        self.printer = config.get_printer()
        self.interval_secs = config.getint("interval", 60, minval=10)
        self.details = NetworkDetails()

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.refresh_thread = None
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.printer.register_event_handler(
            "klippy:disconnect", self._handle_disconnect
        )
    
    @staticmethod
    def get_ssid(iface: str = "wlan0") -> str | None:
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
            os.unlink(client)
        
        return None

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

        eth0_data = InterfaceDetails.from_snicaddrs(network_addrs.get("eth0", []))
        details.ethip = eth0_data.ipv4 or eth0_data.ipv6 or details.ethip

        wifi0_data = InterfaceDetails.from_snicaddrs(network_addrs.get("wlan0", []))
        details.wifiip = wifi0_data.ipv4 or wifi0_data.ipv6 or details.wifiip

        if (ssid := self.get_ssid("wlan0")) is not None:
            details.wifissid = ssid

        try:
            details.mdns = socket.gethostname() + ".local"
        except Exception:
            pass

        details.status = (
            "Connected"
            if details.ethip != "N/A" or details.wifiip != "N/A"
            else "Disconnected"
        )

        with self.lock:
            self.details = details

    def get_status(self, eventtime) -> dict:
        """
        Klipper call method

        :return: Network details
        """
        with self.lock:
            return asdict(self.details)


def load_config(config):
    return network_status(config)

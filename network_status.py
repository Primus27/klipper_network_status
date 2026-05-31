import os
import logging
from dataclasses import dataclass, asdict
from typing import Literal
import socket
import threading

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
        self.interval_secs = config.getint('interval', 60, minval=10)
        self.details = NetworkDetails()
        
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.refresh_thread = None
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.printer.register_event_handler("klippy:disconnect", self._handle_disconnect)

    def _handle_ready(self):
        """
        Refresh network info on a background thread so the blocking subprocess calls never stall Klipper's main thread
        """
        self.stop_event.clear()
        self.refresh_thread = threading.Thread(
            target=self._refresh_loop,
            name="network_status"
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

        try:
            details.ethip = os.popen('ip addr show eth0').read().split("inet ")[1].split("/")[0]
        except Exception:
            pass

        try:
            details.wifiip = os.popen('ip addr show wlan0').read().split("inet ")[1].split("/")[0]
            details.wifissid = os.popen('iwgetid -r').read()[:-1]
        except Exception:
            pass

        try:
            details.mdns = socket.gethostname() + '.local'
        except Exception:
            pass

        details.status = "Connected" if details.ethip != "N/A" or details.wifiip != "N/A" else "Disconnected"

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

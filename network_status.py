import os
import logging
from dataclasses import dataclass, asdict
from typing import Literal

@dataclass
class NetworkDetails:
    status: Literal["Connected", "Disconnected", "N/A"] = "N/A"
    ethip: str = "N/A"
    wifiip: str = "N/A"
    wifissid: str = "N/A"
    mdns: str = "N/A"


class network_status:
    def __init__(self, config):
        self.interval = config.getint('interval', 60, minval=10)
        self.DEFAULT_OUTPUT = "N/A"
        self.details = NetworkDetails()
        self.last_eventtime = 0

    def get_status(self, eventtime):
        if eventtime - self.last_eventtime > self.interval:
            self.details = NetworkDetails()  # Reset network details
            self.last_eventtime = eventtime

            logging.info("network_status get_status %d" % eventtime)
            try:
                self.details.ethip = os.popen('ip addr show eth0').read().split("inet ")[1].split("/")[0]
            except:
                pass

            try:
                self.details.wifiip = os.popen('ip addr show wlan0').read().split("inet ")[1].split("/")[0]
                self.details.wifissid = os.popen('iwgetid -r').read()[:-1]
            except:
                pass

            try:
                self.details.mdns = os.popen('hostname').read()[:-1] + '.local'
            except:
                pass

            self.details.status = "Connected" if self.details.ethip != "N/A" or self.details.wifiip != "N/A" else "Disconnected"

        return asdict(self.details)

def load_config(config):
    return network_status(config)

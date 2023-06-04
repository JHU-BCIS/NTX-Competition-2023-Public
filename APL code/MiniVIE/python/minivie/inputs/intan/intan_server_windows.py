#!/usr/bin/env python3
import asyncio
import binascii
import logging
import socket
import struct
import time

from bleak import BleakClient
from bleak.exc import BleakError
from utilities import user_config as uc

__version__ = "1.0.0"


logger = logging.getLogger("intan_server_windows")


class IntanUdpServer(object):
    def __init__(self, data_logger=None, name="Intan"):

        # These are defaults but can be changed prior to connecting
        self.iface = 0
        self.mac_address = uc.get_user_config_var(
            "IntanUdpServer.mac_address_1", "xx:xx:xx:xx:xx:xx"
        )
        self.local_port = ("localhost", 16001)
        self.remote_port = ("localhost", 15001)

        # Setup file and console logging
        self.logger = data_logger
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = 0
        fh = logging.FileHandler(
            "EMG_MAC_{}_PORT_{}.log".format(
                self.mac_address.replace(":", ""), self.remote_port[1]
            )
        )
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        fh.setFormatter(logging.Formatter("%(created)f %(message)s"))
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        # Create data object handles
        self.peripheral = None
        self.sock = None
        send_udp = lambda data: self.sock.sendto(data, self.remote_port)
        self.delegate = IntanDelegate(send_udp, self.logger)
        self.loop = asyncio.get_event_loop()

    async def run(self):
        # connect bluetooth
        # Make this a blocking call that overrides timeout to ensure connection order
        self.logger.info("Connecting to: " + self.mac_address)

        # This blocks until device is awake and connection established
        while True:
            async with BleakClient(self.mac_address, loop=self.loop) as self.peripheral:
                x = await self.peripheral.is_connected()
                self.logger.info("Connected: {0}".format(x))

                svcs = await self.peripheral.get_services()
                chs = svcs.characteristics

                for uuid in chs:
                    if "notify" in chs[uuid].properties:
                        await self.peripheral.start_notify(
                            uuid, self.delegate.handle_notification
                        )

                # connect udp
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.setblocking(False)
                self.sock.bind(self.local_port)
                self.sock.setblocking(False)

                # start run loop
                status_msg_rate = 2.0  # seconds
                t_start = time.time()

                while True:
                    t_now = time.time()
                    t_elapsed = t_now - t_start

                    if t_elapsed > status_msg_rate:
                        rate_intan = self.delegate.counter["emg"] / t_elapsed
                        status = "MAC: %s Port: %d EMG: %4.1f Hz BattEvts: %d" % (
                            self.mac_address,
                            self.remote_port[1],
                            rate_intan,
                            self.delegate.counter["battery"],
                        )
                        self.logger.info(status)

                        # reset timer and rate counters
                        t_start = t_now
                        self.delegate.counter["emg"] = 0

                    try:
                        data, address = self.sock.recvfrom(1024)
                        if (data[0] == 0) & (len(data) == 2):
                            # Send vibration
                            logging.warning("Sending Intan vibration command")
                            duration = int(data[1])
                            if 0 <= duration <= 3:
                                self.peripheral.writeCharacteristic(
                                    0x19, struct.pack("3b", 0x03, 0x01, duration), True
                                )
                        elif (data[0] == 1) & (len(data) == 1):
                            # Send Deep sleep
                            logging.warning("Sending Intan to deep sleep")
                            self.peripheral.writeCharacteristic(
                                0x19, struct.pack("2b", 0x04, 0x01), True
                            )

                    except BlockingIOError:
                        pass

                    except ConnectionResetError:
                        pass

    def start(self):
        self.loop.run_until_complete(self.run())

    def close(self):
        self.sock.close()


class IntanDelegate:
    # TODO: Currently this only supports udp streaming.  consider internal buffer for udp-free mode (local)

    def __init__(self, send_udp, raw_logger=None):
        self.send_udp = send_udp
        self.num_samples_per_packet = 3
        self.counter = {"emg": 0, "battery": 0}
        self.logger = raw_logger

    def handle_notification(self, sender, data):
        if sender == "00002a19-0000-1000-8000-00805f9b34fb":
            self.send_udp(data)
            self.counter["emg"] += self.num_samples_per_packet
            self.logger.debug("EMG: " + binascii.hexlify(data).decode("utf-8"))
        else:
            self.logger.warning("Got Unknown Notification: %d" % sender)


def setup_threads():
    # get parameters from xml files and create Servers
    s1 = IntanUdpServer(data_logger=logging.getLogger("Intan1"), name="Intan1")

    if uc.get_user_config_var("IntanUdpServer.num_devices", 2) < 2:
        s2 = None
        return s1, s2

    s2 = IntanUdpServer(data_logger=logging.getLogger("Intan2"), name="Intan2")

    return s1, s2


def main():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """
    import argparse
    import sys

    # Parameters:
    parser = argparse.ArgumentParser(
        description="intan_server: read bluetooth packets from intan and stream to UDP."
    )
    parser.add_argument(
        "-x", "--XML", help=r"XML Parameter File (e.g. user_config.xml)", default=None
    )
    args = parser.parse_args()

    if args.XML is not None:
        uc.read_user_config_file(file=args.XML)

        s1, s2 = setup_threads()

        if s2 is None:
            logger.info("Starting Device #1")
            s1.start()
        else:
            logger.info("Starting Device #1")
            s1.start()
            logger.info("Starting Device #2")
            s2.start()
            logger.info("Both Connected")

    logger.info(sys.argv[0] + " Version: " + __version__)


if __name__ == "__main__":
    # Configure logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        main()
    except BleakError as e:
        logger.error(e)

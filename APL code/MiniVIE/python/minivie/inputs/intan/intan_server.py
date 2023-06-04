#!/usr/bin/env python3
"""

This module is a linux based application for establishing an intan sleeve streaming as a server via UDP
This relies on the bluepy module for linux

Typical use would be to set this up as a service on a linux system to continually scan
for intan sleeves and stream data as available

Setting up service (on raspberry pi):

Create the service file
    $ sudo nano /etc/systemd/system/mpl_intan1.service

------------------------- mpl_intan1.service ------------------------------
[Unit]
Description=Intan Streamer
Requires=bluetooth.target
After=network.target bluetooth.target

[Service]
ExecStart=/usr/bin/python3.7 -u -m inputs.intan.intan_server -x vmpl_user_config.xml
WorkingDirectory=/home/pi/git/minivie/python/minivie
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
------------------------- mpl_intan1.service ------------------------------

Enable the service

    $ sudo systemctl enable mpl_intan1.service

    Created symlink from /etc/systemd/system/multi-user.target.wants/mpl_intan1.service to /lib/systemd/system/mpl_intan1.service.

Start service and check status

    $ sudo systemctl start mpl_intan1.service
    $ sudo systemctl status mpl_intan1.service
    ● mpl_intan1.service - Intan Streamer
       Loaded: loaded (/etc/systemd/system/mpl_intan1.service; enabled; vendor preset: enabled)
       Active: active (running) since Thu 2018-08-16 03:54:51 UTC; 5s ago
     Main PID: 942 (python3)
       CGroup: /system.slice/mpl_intan1.service
               ├─942 /usr/bin/python3.7 -u -m inputs.intan_server -x vmpl_user_config.xml
               └─951 /usr/local/lib/python3.7/dist-packages/bluepy/bluepy-helper 0

    Aug 16 03:54:51 raspberrypi systemd[1]: Started Intan Streamer.

"""

import binascii
import logging
import socket
import struct
import time

from bluepy import btle

from utilities import get_address
from utilities import user_config as uc

__version__ = "1.0.0"


class IntanUdpServer(object):

    def __init__(self, name='Intan'):
        self.name = name

        # These are defaults but can be changed prior to connecting
        self.iface = 0
        self.mac_address = 'XX:XX:XX:XX:XX:XX'  # note this needs to be upper when finding handle to peripheral
        self.local_port = ('localhost', 16001)
        self.remote_port = ('localhost', 15001)

        # Setup file and console logging
        self.logger = None

        # Create data object handles
        self.peripheral = None
        self.sock = None
        self.delegate = None
        self.thread = None

    def setup_devices(self):
        # Create data object handles
        import threading
        import subprocess

        send_udp = lambda data: self.sock.sendto(data, self.remote_port)
        self.delegate = IntanDelegate(send_udp, self.logger)
        self.thread = threading.Thread(target=self.run)
        self.thread.name = self.name

        self.logger.debug('Running subprocess command: hcitool dev')
        hci = 'hci' + str(self.iface)

        # Note that if running from startup, you should require bluetooth.target
        # to ensure that the bluetooth device is started
        output = subprocess.check_output(["hcitool", "dev"])
        if hci in output.decode('utf-8'):
            self.logger.info('Found device: ' + hci)
        else:
            self.logger.info('Device not found: ' + hci)

    def setup_logger(self):
        # Setup file and console logging
        # Note this should occur after MAC address assigned since that is used for the filename
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = 0
        fh = logging.FileHandler(
            'EMG_MAC_{}_PORT_{}.log'.format(self.mac_address.replace(':', ''), self.remote_port[1]))
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        fh.setFormatter(logging.Formatter('%(created)f %(message)s'))
        ch.setFormatter(logging.Formatter("[%(threadName)-s] [%(levelname)-5.5s]  %(message)s"))
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def set_device_parameters(self):
        """function parameters"""
        # Notifications are unacknowledged, while indications are acknowledged. Notifications are therefore faster,
        # but less reliable.
        # Indication = 0x02; Notification = 0x01

        write = self.peripheral.writeCharacteristic

        self.peripheral.setMTU(64)

        # Set up main streaming
        characteristics = self.peripheral.getCharacteristics()

        for characteristic in characteristics:
            if 'NOTIFY' in characteristic.propertiesToString():
                write(characteristic.getHandle() + 1, struct.pack('<bb', 1, 0), 1)  # Subscribe to all notifications
                self.logger.info('Subscribed to characteristic: {}'.format(characteristic.getHandle()))

    def set_host_parameters(self):
        """
            Set parameters on the host adapter to allow low-latency streaming

            The command sets the Preferred Peripheral Connection Parameters (PPCP).  You can find summary Bluetooth
            information here: https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.
                characteristic.gap.peripheral_preferred_connection_parameters.xml

            Breaking down the command "sudo hcitool cmd 0x08 0x0013 40 00 06 00 06 00 00 00 90 01 00 00 07 00"

            the syntax for the 'cmd' option in 'hcitool' is:
                hcitool cmd <ogf> <ocf> [parameters]

                OGF: 0x08 "7.8 LE Controller Commands"

                OCF: 0x0013 "7.8.18 LE Connection Update Command"

            The significant command parameter bytes are "06 00 06 00 00 00 90 01" (0x0006, 0x0006, 0x0000, 0x0190)

            These translate to setting the min, and max Connection Interval to 0x0006=6;6*1.25ms=7.5ms, with no slave
                latency, and a 0x0190=400; 400*10ms=4s timeout.
            UPDATE: Added non-zero slave latency for robustness on DART board

            For more info, you can search for the OGF, OCF sections listed above in the Bluetooth Core 4.2 spec

        """
        import subprocess

        # get the connection information
        conn_raw = subprocess.check_output(['hcitool', 'con'])

        # parse to get our connection handle
        conn_lines = conn_raw.decode('utf-8').split('\n')

        handle_hex = None
        for conn in conn_lines:
            if conn.find(self.mac_address) > 0:
                start = 'handle'
                end = 'state'
                handle = int(conn.split(start)[1].split(end)[0])
                handle_hex = '{:04x}'.format(handle)
                self.logger.info('MAC: {} is handle {}'.format(self.mac_address, handle))

        if handle_hex is None:
            logging.error('Connection not found while setting adapter rate')
            return

        cmd_str = "hcitool -i hci{} cmd 0x08 0x0013 {} {} 06 00 06 00 00 00 90 01 01 00 07 00".format(
            self.iface, handle_hex[2:], handle_hex[:2])
        self.logger.info("Setting host adapter update rate: " + cmd_str)
        # subprocess.Popen(cmd_str, shell=True)
        subprocess.run(cmd_str, shell=True)

    def connect(self):
        # connect bluetooth
        # Make this a blocking call that overrides timeout to ensure connection order
        self.logger.info("Connecting to: " + self.mac_address)

        # This blocks until device is awake and connection established
        self.peripheral = btle.Peripheral()
        while True:
            try:
                self.peripheral.connect(self.mac_address, addrType=btle.ADDR_TYPE_PUBLIC, iface=self.iface)
                print('Connection Successful')
                break
            except btle.BTLEException:
                print('Timed out while connecting to device at address {}'.format(self.mac_address))

        self.set_device_parameters()

        # connect udp
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(self.local_port)

        # Assign event handler
        self.peripheral.withDelegate(self.delegate)

    def run(self):

        # start run loop
        status_msg_rate = 2.0  # seconds
        t_start = time.time()

        while True:
            t_now = time.time()
            t_elapsed = t_now - t_start

            #  waitForNotifications(timeout) Blocks until a notification is received from the peripheral
            # or until the given timeout (in seconds) has elapsed
            if not self.peripheral.waitForNotifications(1.0):
                self.logger.warning('Missed Intan notification.')

            if t_elapsed > status_msg_rate:
                rate_intan = self.delegate.counter['emg'] / t_elapsed
                status = "MAC: %s Port: %d EMG: %4.1f Hz BattEvts: %d" % (
                    self.mac_address, self.remote_port[1], rate_intan, self.delegate.counter['battery'])
                self.logger.info(status)

                # reset timer and rate counters
                t_start = t_now
                self.delegate.counter['emg'] = 0

            # Check for receive messages
            #
            # Define a simple protocol for commands to Intan
            #
            # Message ID:
            # 0 - Send vibration. Expects a 1 byte payload with duration
            # 1 - Send intan to Deep Sleep
            #
            # Send a single byte for vibration command with duration of 0-3 seconds
            # s.sendto(bytearray([2]),('localhost',16001))
            #
            # import socket
            # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # sock.bind(('0.0.0.0', 9097))
            # sock.sendto(bytearray([0, 2]), ('127.0.0.1', 16001))
            # sock.sendto(bytearray([1]), ('127.0.0.1', 16001))

            try:
                data, address = self.sock.recvfrom(1024)

                if data:
                    vibe_unpacker = struct.Struct("3B")
                    vibe_cmd = vibe_unpacker.unpack(data)
                    duration = int(vibe_cmd[0])
                    intensity = int(vibe_cmd[1])
                    motor_mask = int(vibe_cmd[2])

                    # Send vibration
                    logging.info('Sending Intan vibration command')

                    if 0 <= duration <= 3:
                        self.peripheral.writeCharacteristic(0x0e, struct.pack(
                            '3B', duration, intensity, motor_mask), True)
            except struct.error as e:
                print(f"Error unpacking data: {e}")
            except socket.timeout:
                pass
            except BlockingIOError:
                pass

    def close(self):
        self.sock.close()


class IntanDelegate(btle.DefaultDelegate):
    """
    Callback function for handling incoming data from bluetooth connection

    """

    # TODO: Currently this only supports udp streaming.  consider internal buffer for udp-free mode (local)

    def __init__(self, send_udp, raw_logger=None):
        self.send_udp = send_udp
        self.num_samples_per_packet = 3
        self.counter = {'emg': 0, 'battery': 0}
        self.logger = raw_logger
        super(IntanDelegate, self).__init__()

    def handleNotification(self, ch_handle, data):
        if ch_handle == 0xc:  # EmgDataCharacteristic
            self.send_udp(data)
            self.counter['emg'] += self.num_samples_per_packet
            self.logger.debug('EMG: ' + binascii.hexlify(data).decode('utf-8'))
        else:
            self.logger.warning('Got Unknown Notification: %d' % ch_handle)

        return


def setup_threads():
    # get parameters from xml files and create Servers
    s1 = IntanUdpServer(name='Intan1')
    s1.iface = uc.get_user_config_var("IntanUdpServer.iface_1", 0)
    s1.mac_address = uc.get_user_config_var("IntanUdpServer.mac_address_1", 'XX:XX:XX:XX:XX:XX')
    local_port_str = uc.get_user_config_var("IntanUdpServer.local_address_1", '//0.0.0.0:16001')
    s1.local_port = get_address(local_port_str)
    remote_port_str = uc.get_user_config_var("IntanUdpServer.remote_address_1", '//127.0.0.1:15001')
    s1.remote_port = get_address(remote_port_str)
    s1.setup_logger()
    s1.setup_devices()

    if uc.get_user_config_var('IntanUdpServer.num_devices', 2) < 2:
        s2 = None
        return s1, s2

    s2 = IntanUdpServer(name='Intan2')
    s2.iface = uc.get_user_config_var("IntanUdpServer.iface_2", 0)
    s2.mac_address = uc.get_user_config_var("IntanUdpServer.mac_address_2", 'XX:XX:XX:XX:XX:XX')
    local_port_str = uc.get_user_config_var("IntanUdpServer.local_address_2", '//0.0.0.0:16002')
    s2.local_port = get_address(local_port_str)
    remote_port_str = uc.get_user_config_var("IntanUdpServer.remote_address_2", '//127.0.0.1:15002')
    s2.remote_port = get_address(remote_port_str)
    s2.setup_logger()
    s2.setup_devices()

    return s1, s2


def main():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """
    import sys
    import argparse

    # Parameters:
    parser = argparse.ArgumentParser(description='intan_server: read bluetooth packets from intan and stream to UDP.')
    parser.add_argument('-x', '--XML', help=r'XML Parameter File (e.g. user_config.xml)',
                        default=None)
    args = parser.parse_args()

    if args.XML is not None:
        uc.read_user_config_file(file=args.XML)
        s1, s2 = setup_threads()

        if s2 is None:
            print(f'Connecting Device #1:{s1.mac_address}')
            s1.connect()
            time.sleep(0.5)
            s1.thread.start()
            time.sleep(0.5)
            s1.set_host_parameters()
        else:
            print(f'Connecting Device #1:{s1.mac_address}')
            s1.connect()
            print(f'Connecting Device #2:{s2.mac_address}')
            s2.connect()
            print('Both Connected. Starting Threads')

            time.sleep(0.5)
            s1.thread.start()
            time.sleep(0.5)
            s2.thread.start()
            time.sleep(1.5)
            s2.set_host_parameters()
            time.sleep(0.5)
            s1.set_host_parameters()

    print(sys.argv[0] + " Version: " + __version__)


if __name__ == '__main__':
    main()

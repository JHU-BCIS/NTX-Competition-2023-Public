# myo UDP server using the cross-platform bleak bluetooth interface package
# This code was contributed on the TekBlue/minivieextended project fork
#
# Command line usage: 
#   From the python/minivie/inputs/myo directory:
#   py myo_server_bleak.py -x user_config.xml
#   From the python/minivie/inputs/myo directory:
#   py -m inputs.myo.myo_server_bleak -x user_config_default.xml
#
# Note: results can then be visualized using:
#   py python\minivie\gui\test_live_plot.py

import os
import logging
import time
import socket
import binascii
import platform
import sys
import argparse
import asyncio
from bleak import BleakClient
from bleak import BleakError

# Ensure that the project modules can be found on path allowing execution from the 'myo' folder
if os.path.split(os.getcwd())[1] == 'myo':
    sys.path.insert(0, os.path.abspath(os.path.join('..', '..')))
from utilities import user_config as uc
from utilities import get_address


__version__ = "1.2.0"


class UdpSender(object):
    def __init__(self,
                 local_port="//127.0.0.1:16001",
                 remote_ports="//127.0.0.1:15001"):
        self.local_port = get_address(local_port)
        self.remote_ports = []
        print(remote_ports)
        remote_ports_tuple = remote_ports.split(",")
        print(remote_ports_tuple)
        for remote_port in remote_ports_tuple:
            self.remote_ports.append(get_address(remote_port))

        for remote_port in self.remote_ports:
            print(remote_port)
        self.sock = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(self.local_port)

    def send(self, data):
        for remote_port in self.remote_ports:
            self.sock.sendto(data, remote_port)


class MyoBluetoothInterface(object):
    def __init__(self):
        self.control_service                    = "d5060001-a904-deb9-4748-2c7f4a124842"
        self.myo_info_characteristic            = "d5060101-a904-deb9-4748-2c7f4a124842"
        self.firmware_version_characteristic    = "d5060201-a904-deb9-4748-2c7f4a124842"
        self.command_characteristic             = "d5060401-a904-deb9-4748-2c7f4a124842"
        self.imu_data_service                   = "d5060002-a904-deb9-4748-2c7f4a124842"
        self.imu_data_characteristic            = "d5060402-a904-deb9-4748-2c7f4a124842"
        self.motion_event_characteristic        = "d5060502-a904-deb9-4748-2c7f4a124842"
        self.classifier_service                 = "d5060003-a904-deb9-4748-2c7f4a124842"
        self.classifier_event_characteristic    = "d5060103-a904-deb9-4748-2c7f4a124842"
        self.emg_data_service                   = "d5060005-a904-deb9-4748-2c7f4a124842"
        self.emg_data_0_characteristic          = "d5060105-a904-deb9-4748-2c7f4a124842"
        self.emg_data_1_characteristic          = "d5060205-a904-deb9-4748-2c7f4a124842"
        self.emg_data_2_characteristic          = "d5060305-a904-deb9-4748-2c7f4a124842"
        self.emg_data_3_characteristic          = "d5060405-a904-deb9-4748-2c7f4a124842"

        # Standard Bluetooth services
        self.battery_service = "0000180f-0000-1000-8000-00805f9b34fb"
        self.battery_level_characteristic = "00002a19-0000-1000-8000-00805f9b34fb"
        self.device_name = "00002a00-0000-1000-8000-00805f9b34fb"

        # Commands
        self.command_set_mode = 0x01
        self.command_vibrate = 0x03
        self.command_deep_sleep = 0x04
        self.command_vibrate2 = 0x07
        self.command_set_sleep_mode = 0x09
        self.command_unlock = 0x0a
        self.command_user_action = 0x0b

        # EMG mode
        self.emg_mode_none = 0x00  # Do not send EMG data.
        self.emg_mode_send_emg = 0x02  # Send filtered EMG data.
        self.emg_mode_send_emg_raw = 0x03  # Send raw (unfiltered) EMG data.

        # IMU mode
        self.imu_mode_none = 0x00  # Do not send IMU data or events.
        self.imu_mode_send_data = 0x01  # Send IMU data streams(accelerometer, gyroscope, and orientation).
        self.imu_mode_send_events = 0x02  # Send motion events detected by the IMU(e.g.taps).
        self.imu_mode_send_all = 0x03  # Send both IMU data streams and motion events.
        self.imu_mode_send_raw = 0x04  # Send raw IMU data streams.

        # Classifier mode
        self.classifier_mode_disabled = 0x00  # Disable and reset the internal state of the onboard classifier.
        self.classifier_mode_enabled = 0x01  # Send classifier events(poses and arm events).

        # Vibration mode
        self.vibration_none = 0x00  # Do not vibrate.
        self.vibration_short = 0x01  # Vibrate for a short amount of time.
        self.vibration_medium = 0x02  # Vibrate for a medium amount of time.
        self.vibration_long = 0x03  # Vibrate for a long amount of time.

        # Sleep mode
        self.sleep_mode_normal = 0  # Normal sleep mode; Myo will sleep after a period of inactivity.
        self.sleep_mode_never_sleep = 1  # Never go to sleep


# noinspection PyTypeChecker
class MyoUdpServer(object):

    def __init__(self,
                 bluetooth_hardware_interface=0,
                 mac_address='xx:xx:xx:xx:xx:xx',
                 local_port=('localhost', 16001),
                 remote_ports='//localhost:15001',
                 data_logger=None,
                 name='Myo'):

        self.name = name
        self.stay_connected = True
        # Create Bluetooth properties
        self.bluetooth_hardware_interface = bluetooth_hardware_interface
        self.mac_address = mac_address.upper()
        self.myo_bluetooth_interface = MyoBluetoothInterface()
        self.bluetooth_client = BleakClient(self.mac_address)
        self.bleakLogging = logging.getLogger("bleak")
        self.bleakLogging.setLevel(logging.CRITICAL)
        self.iface = 0

        # Create UDP networking properties
        self.udp_sender = UdpSender(local_port=local_port, remote_ports=remote_ports)

        # UDP counter
        self.counter = {'emg': 0, 'imu': 0, 'battery': 0}

        # Setup file and console logging
        self.logger = data_logger
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = 0
        fh = logging.FileHandler(
            'EMG_MAC_{}_PORT_{}.log'.format(self.mac_address.replace(':', ''), self.udp_sender.remote_ports[0][1]))
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('%(created)f %(message)s'))
        ch.setFormatter(logging.Formatter("[%(threadName)-s] [%(levelname)-5.5s]  %(message)s"))
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def bluetooth_notification_handler(self, sender, data):

        sender_uuid = self.get_uuid(sender)

        if sender_uuid == self.myo_bluetooth_interface.emg_data_0_characteristic:
            self.send_emg_data(0, data)
            return
        elif sender_uuid == self.myo_bluetooth_interface.emg_data_1_characteristic:
            self.send_emg_data(1, data)
            return
        elif sender_uuid == self.myo_bluetooth_interface.emg_data_2_characteristic:
            self.send_emg_data(2, data)
            return
        elif sender_uuid == self.myo_bluetooth_interface.emg_data_3_characteristic:
            self.send_emg_data(3, data)
            return
        elif sender_uuid == self.myo_bluetooth_interface.imu_data_characteristic:
            self.send_imu_data(data)
            return
        elif sender_uuid == self.myo_bluetooth_interface.battery_level_characteristic:
            self.send_battery_data(data)
            return

        print("Unknown notification Sender: {0} UUID: {1} Data: {2}".format(sender, sender_uuid, data))

    def get_uuid(self, sender):
        return self.bluetooth_client.services.characteristics.get(sender).uuid

    def send_emg_data(self, channel, data):
        self.logger.debug('EMG {0}: {1}'.format(channel, binascii.hexlify(data).decode('utf-8')))
        self.counter['emg'] += 2
        self.udp_sender.send(data)

    def send_imu_data(self, data):
        self.logger.debug('IMU: ' + binascii.hexlify(data).decode('utf-8'))
        self.counter['imu'] += 1
        self.udp_sender.send(data)

    def send_battery_data(self, data):
        self.logger.debug('BATTERY: ' + binascii.hexlify(data).decode('utf-8'))
        self.counter['battery'] += 1
        self.udp_sender.send(data)

    async def start(self):
        await self.init_myo_connection()
        await self.ensure_connection()

    async def init_myo_connection(self):
        await self.connect()
        self.set_host_parameters()
        await self.vibrate_myo()
        await self.disable_myo_sleep()
        await self.enable_myo_emg_notification()
        await self.enable_myo_imu_notification()
        # TODO: Battery Notification does not work in bluez
        # await self.enable_battery_notification()
        await self.set_myo_notification_data_modes()

    async def connect(self):
        self.logger.info("Connecting to device {0} {1}".format(self.name, self.mac_address))
        connecting = True
        while connecting:
            try:
                await self.bluetooth_client.connect()
                connecting = False
            except BleakError:
                self.logger.warning("Could not find device {0} {1} Re-Trying".format(self.name, self.mac_address))
                pass
        self.logger.info("Device connected {0} {1}".format(self.name, self.mac_address))

    async def vibrate_myo(self):
        payload = bytes([self.myo_bluetooth_interface.command_vibrate, 1, self.myo_bluetooth_interface.vibration_long])
        await self.bluetooth_client.write_gatt_char(self.myo_bluetooth_interface.command_characteristic, payload)

    async def disable_myo_sleep(self):
        payload = bytes([self.myo_bluetooth_interface.command_set_sleep_mode, 1,
                         self.myo_bluetooth_interface.sleep_mode_never_sleep])
        await self.bluetooth_client.write_gatt_char(self.myo_bluetooth_interface.command_characteristic, payload)

    async def disable_myo_motion_notification(self):
        await self.bluetooth_client.stop_notify(self.myo_bluetooth_interface.motion_event_characteristic)

    async def enable_myo_emg_notification(self):
        await self.bluetooth_client.start_notify(self.myo_bluetooth_interface.emg_data_0_characteristic,
                                                 self.bluetooth_notification_handler)
        await self.bluetooth_client.start_notify(self.myo_bluetooth_interface.emg_data_1_characteristic,
                                                 self.bluetooth_notification_handler)
        await self.bluetooth_client.start_notify(self.myo_bluetooth_interface.emg_data_2_characteristic,
                                                 self.bluetooth_notification_handler)
        await self.bluetooth_client.start_notify(self.myo_bluetooth_interface.emg_data_3_characteristic,
                                                 self.bluetooth_notification_handler)

    async def enable_myo_imu_notification(self):
        await self.bluetooth_client.start_notify(self.myo_bluetooth_interface.imu_data_characteristic,
                                                 self.bluetooth_notification_handler)

    async def set_myo_notification_data_modes(self):
        payload = bytes([self.myo_bluetooth_interface.command_set_mode, 3,
                         self.myo_bluetooth_interface.emg_mode_send_emg_raw,
                         self.myo_bluetooth_interface.imu_mode_send_data,
                         self.myo_bluetooth_interface.classifier_mode_disabled])
        await self.bluetooth_client.write_gatt_char(self.myo_bluetooth_interface.command_characteristic, payload)

    async def enable_battery_notification(self):
        await self.bluetooth_client.start_notify(self.myo_bluetooth_interface.battery_level_characteristic,
                                                 self.bluetooth_notification_handler)

    async def print_services_characteristics(self):
        services = await self.bluetooth_client.get_services()

        for service in services:
            self.logger.info("Service: {0} {1}".format(service.description, service.uuid))
            characteristics = service.characteristics
            for characteristic in characteristics:
                self.logger.info("--- Characteristic: {0} {1}".format(characteristic.description, characteristic.uuid))

    async def ensure_connection(self):

        status_msg_rate = 8.0  # seconds
        t_start = time.time()

        while self.stay_connected:
            t_now = time.time()
            t_elapsed = t_now - t_start

            #  waitForNotifications(timeout) Blocks until a notification is received from the peripheral
            # or until the given timeout (in seconds) has elapsed

            if t_elapsed > status_msg_rate:
                rate_myo = self.counter['emg'] / t_elapsed
                rate_imu = self.counter['imu'] / t_elapsed
                status = "MAC: %s Port: %d EMG: %4.1f Hz IMU: %4.1f Hz BattEvts: %d" % (
                    self.mac_address, self.udp_sender.remote_ports[0][1], rate_myo, rate_imu, self.counter['battery'])
                self.logger.info(status)

                # reset timer and rate counters
                t_start = t_now
                self.counter['emg'] = 0
                self.counter['imu'] = 0

            # git\minivie\python\minivie\inputs\myo\myo_server_bleak.py:303:
            # FutureWarning: is_connected has been changed to a property.
            # Calling it as an async method will be removed in a future version
            #   if not await self.bluetooth_client.is_connected():
            if not self.bluetooth_client.is_connected:
                self.logger.warning(
                    "Device disconnected retrying connection {0} {1}".format(self.name, self.mac_address))
                await self.bluetooth_client.disconnect()
                self.bluetooth_client = BleakClient(self.mac_address)
                await self.init_myo_connection()

            await asyncio.sleep(1)

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

        if platform.system() != "linux":
            return

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


def get_myo_servers():
    myo_servers = []
    # get parameters from xml files and create Servers
    s1 = MyoUdpServer(bluetooth_hardware_interface=uc.get_user_config_var('MyoUdpServer.iface_1', 0),
                      mac_address=uc.get_user_config_var('MyoUdpServer.mac_address_1', 'xx:xx:xx:xx:xx'),
                      local_port=uc.get_user_config_var('MyoUdpServer.local_address_1', '//127.0.0.1:16001'),
                      remote_ports=uc.get_user_config_var('MyoUdpServer.remote_address_1', '//127.0.0.1:15001'),
                      data_logger=logging.getLogger('Myo1'),
                      name='Myo1')

    myo_servers.append(s1)
    if uc.get_user_config_var('MyoUdpServer.num_devices', 2) > 1:
        s2 = MyoUdpServer(bluetooth_hardware_interface=uc.get_user_config_var('MyoUdpServer.iface_2', 0),
                          mac_address=uc.get_user_config_var('MyoUdpServer.mac_address_2', 'xx:xx:xx:xx:xx'),
                          local_port=uc.get_user_config_var('MyoUdpServer.local_address_2', '//127.0.0.1:16002'),
                          remote_ports=uc.get_user_config_var('MyoUdpServer.remote_address_2', '//127.0.0.1:15002'),
                          data_logger=logging.getLogger('Myo2'),
                          name='Myo2')
        myo_servers.append(s2)

    return myo_servers


async def start_myo_servers(loop):
    myo_servers = get_myo_servers()

    if len(myo_servers) > 1:
        for i in range(1, len(myo_servers)):
            loop.create_task(myo_servers[i].start())

    await myo_servers[0].start()


async def start_myo_server(xml_config_path, loop):
    uc.read_user_config_file(file=xml_config_path)
    await start_myo_servers(loop)


def main():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.
    """

    # Parameters:
    parser = argparse.ArgumentParser(description='myo_server: read bluetooth packets from myo and stream to UDP.')
    parser.add_argument('-x',
                        '--XML',
                        help=r'XML Parameter File (e.g. user_config.xml)',
                        default="../user_config_default.xml")
    args = parser.parse_args()
    print(sys.argv[0] + " Version: " + __version__)

    if args.XML is not None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_myo_server(args.XML, loop))
        loop.close()


if __name__ == '__main__':
    main()

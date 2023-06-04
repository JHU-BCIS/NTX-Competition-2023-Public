# Connect to a Bluetooth device and read its model number and properties, vibrate, then shut off:
#
# Shut off myo:
#   py demo_myo_interface.py MAC:AD:DR:ESS

import sys
import asyncio
from bleak import BleakClient
from myo_server_bleak import MyoBluetoothInterface
import struct

if len(sys.argv) < 2:
    print('Usage: py demo_myo_interface.py MAC:AD:DR:ESS')
    sys.exit()
    
address = str(sys.argv[1])

myo = MyoBluetoothInterface()


async def run(address, loop):
    async with BleakClient(address, loop=loop, timeout=10.0) as client:

        # Get Firmware Version
        result = await client.read_gatt_char(myo.firmware_version_characteristic)
        version = struct.unpack('<HHHH', result)
        print(f"Firmware Version: Major.Minor.Patch {version[0]}.{version[1]}.{version[2]}  Hardware Rev{version[3]}")

        # Turn off sleep
        print('Turning off sleep mode')
        await client.write_gatt_char(myo.command_characteristic, bytearray([myo.command_set_sleep_mode, 1, myo.sleep_mode_never_sleep]))

        # vibrate_myo
        print('Vibrating')
        await client.write_gatt_char(myo.command_characteristic, bytearray([myo.command_vibrate, 1, myo.vibration_long]))

        print('Waiting...')
        await asyncio.sleep(1)

        # deep sleep
        print('Sending myo to deep sleep')
        await client.write_gatt_char(myo.command_characteristic, bytearray([myo.command_deep_sleep, 0]))


loop = asyncio.get_event_loop()
loop.run_until_complete(run(address, loop))

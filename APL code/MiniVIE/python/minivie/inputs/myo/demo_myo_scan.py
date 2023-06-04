# To discover Bluetooth devices that can be connected to:

import asyncio
from bleak import discover

scan_timeout = 5.0


async def func_scan():
    devices = await discover(timeout=scan_timeout)
    myos = []
    for d in devices:
        if 'D5060001-A904-DEB9-4748-2C7F4A124842'.lower() in d.metadata['uuids']:
            print(f'Myo (RSSI={d.rssi}): {d}')
            myos.append(d)
        else:
            print(f'BLE (RSSI={d.rssi}): {d}')

    return devices, myos

loop = asyncio.get_event_loop()
print(f'Scanning for {scan_timeout} seconds...')

tasks = func_scan(),
task_result = loop.run_until_complete(asyncio.gather(*tasks))
# loop.close()
print('Scan Complete')

scan_result = task_result[0]
myos =scan_result[1]

for m in myos:
    print(m)

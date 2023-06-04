import socket
import struct
import time

import numpy as np
import utilities

__version__ = "1.0.0"

num_channels = 8
num_samples_per_packet = 3
num_bytes_per_sample = 2


def emulate_intan_unix(destination="//127.0.0.1:15001"):
    """
    Emulate Intan UNIX streaming outputs for testing

    Example Usage within python:
        import os
        os.chdir(r"C:\git\minivie\python\minivie")
        from inputs.intan import intan_sim
        intan_sim.emulate_intan_unix() # CTRL+C to END

    Example Usage from command prompt:
        python -m inputs.intan.intan_sim.py -SIM_UNIX

    """

    # Multicast Demo
    # ANY = "0.0.0.0"
    # SENDERPORT = 32000
    # MCAST_ADDR = "239.255.1.1"
    # MCAST_PORT = 1600
    #
    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
    #                      socket.IPPROTO_UDP)
    # sock.bind((ANY, SENDERPORT))
    # sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #
    # address = (MCAST_ADDR, MCAST_PORT)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    address = utilities.get_address(destination)
    print("Running IntanUdp Emulator to " + destination)

    # Add listener socket for vibration commands
    listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener_sock.bind(("0.0.0.0", 16001))
    listener_sock.settimeout(0.1)

    try:
        while True:
            # generate random bytes matching the size of IntanUdp.exe streaming
            vals = np.random.randint(
                65535, size=num_bytes_per_sample * num_samples_per_packet * num_channels
            ).astype("uint8")
            sock.sendto(vals.tobytes(), address)

            try:
                data, address = listener_sock.recvfrom(1024)

                if data:
                    vibe_unpacker = struct.Struct("3B")
                    vibe_cmd = vibe_unpacker.unpack(data)
                    duration = int(vibe_cmd[0])
                    intensity = int(vibe_cmd[1])
                    motor_mask = int(vibe_cmd[2])

                    # Send vibration
                    print(
                        f"Sending Intan vibration command: {duration}, {intensity}, {motor_mask}"
                    )
            except struct.error as e:
                print(f"Error unpacking data: {e}")
            except socket.timeout:
                pass

            time.sleep(0.01)  # >200Hz

    except KeyError:
        pass
    print("Closing Intan Emulator")
    sock.close()


def main():
    """Parse command line arguments into argparse model.

    Command-line arguments:
    -h or --help -- output help text describing command-line arguments.

    """
    import argparse
    import sys

    # Parameters:
    parser = argparse.ArgumentParser(
        description="IntanUdp: Read from intan and stream UDP."
    )
    parser.add_argument(
        "-u", "--SIM_UNIX", help="Run UNIX EMG Simulator", action="store_true"
    )
    parser.add_argument(
        "-a",
        "--ADDRESS",
        help=r"Destination Address (e.g. //127.0.0.1:15001)",
        default="//127.0.0.1:15001",
    )
    args = parser.parse_args()

    if args.SIM_UNIX:
        emulate_intan_unix(args.ADDRESS)
    else:
        # No Action
        print(sys.argv[0] + " Version: " + __version__)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from __future__ import with_statement  # 2.5 only

import logging
import struct
import time

import numpy as np
from inputs.signal_input import SignalInput
from utilities import get_address, udp_comms

logger = logging.getLogger("intan_client")


class IntanUdp(SignalInput):
    """
    Class for receiving Intan sleeve data via UDP
    Handles streaming data from Intan sim or streaming data from unix based streaming
    Note the use of private variable and threading / locks to ensure data is read safely
    """

    def __init__(
        self,
        local_addr_str="//0.0.0.0:15001",
        remote_addr_str="//127.0.0.1:16001",
        num_samples=50,
    ):

        # Initialize superclass
        super(IntanUdp, self).__init__()

        # logger
        self.log_handlers = None

        # 3 channels for intan sleeve
        self.num_channels = 8
        self.num_samples = num_samples
        self.num_samples_per_packet = 3

        # Default data buffer [nSamples by nChannels]
        # Treat as private.  use get_data to access since it is thread-safe
        self.__dataEMG = np.zeros((self.num_samples, self.num_channels))

        # Internal values
        self.__battery_level = -1  # initial value is unknown
        self.__rate_emg = 0.0
        self.__count_emg = 0  # reset counter
        self.__time_emg = 0.0
        self.emg_rate_update_interval = 1.5

        # Initialize connection parameters
        self.transport = udp_comms.Udp()
        self.transport.name = "IntanUdpRcv"
        self.transport.local_addr = get_address(local_addr_str)
        self.transport.remote_addr = get_address(remote_addr_str)
        self.transport.add_message_handler(self.parse_messages)

    def connect(self):
        """
        Connect to the udp server and receive Intan Packets
        """
        self.transport.connect()

    def parse_messages(self, data):
        """Convert incoming bytes to emg, quaternion, accel, and ang rate"""

        num_emg_samples = 0

        if (
            len(data) == 2 * self.num_channels * self.num_samples_per_packet
        ):  # EMG data only
            # -------------------------------------
            # Handles data from unix direct stream
            # -------------------------------------
            num_samples = self.num_channels * self.num_samples_per_packet
            output_format = f"<{num_samples}H"
            output = struct.unpack(output_format, data)

            # Scale raw EMG to microvolts
            output = np.array(output)
            output = 0.195 * (output - 32768)

            # Populate EMG Data Buffer (newest on top)
            for i in range(self.num_samples_per_packet):
                self.__dataEMG = np.roll(self.__dataEMG, 1, axis=0)
                self.__dataEMG[:1, :] = output[
                    i * self.num_channels : (i * self.num_channels) + self.num_channels
                ]

            # count samples toward data data rate
            num_emg_samples = self.num_samples_per_packet

        else:
            logger.warning(f"IntanUdp: Unexpected packet size. len=({len(data)})")

        if num_emg_samples == 0:
            return
        else:
            self.__count_emg += num_emg_samples

    def get_data(self):
        """Return data buffer [nSamples][nChannels]"""
        return self.__dataEMG

    def get_battery(self):
        # Return the battery value (0-100)
        battery = self.__battery_level
        return battery

    def get_data_rate_emg(self):
        # Data rate is just EMG rate, not IMU or packet rate and should be calculated accordingly
        # Return the emg data rate

        # compute data rate
        t_now = time.time()
        t_elapsed = t_now - self.__time_emg

        if t_elapsed > self.emg_rate_update_interval:
            # compute rate (every second)
            self.__rate_emg = self.__count_emg / t_elapsed
            self.__count_emg = 0  # reset counter
            # reset time
            self.__time_emg = time.time()

        return self.__rate_emg

    def get_status_msg(self):
        # return string formatted status message
        # with data rate and battery percentage
        # E.g. 200Hz 99%
        battery = self.get_battery()
        if battery < 0:
            battery = "--"
        return f"INTAN: {self.get_data_rate_emg():.0f}Hz {battery}%"

    def close(self):
        self.transport.close()

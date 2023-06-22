#! /usr/bin/python3

# Simple function for converting EMG log file to matlab file
# Requires scipy
#
# To run from command line:
# > python emg_log_parser.py <log_file_path>

import io
import struct
import sys
import time as t
from collections import defaultdict

import scipy.io as spio

NUM_CHANNELS = 8
NUM_SAMPLES_PER_PACKET = 3
STRUCT_FMT = f"<{NUM_CHANNELS * NUM_SAMPLES_PER_PACKET}H"


def parse(filename):
    start_time = t.time()

    m = defaultdict(list)

    with io.open(filename, "r", encoding="utf-8-sig") as log_file:
        for line in log_file:
            try:
                strings = line.split(" ")

                if "EMG:" in strings:
                    data = strings[-1].strip()
                    if len(data) == 2 * 2 * NUM_CHANNELS * NUM_SAMPLES_PER_PACKET:
                        # Append timestamp
                        m["Timestamp"].append(float(strings[0]))

                        # Proper data length
                        hex_data = bytes.fromhex(data)
                        emg_data = struct.unpack(STRUCT_FMT, hex_data)
                        for i in range(NUM_SAMPLES_PER_PACKET):
                            m["EMG"].append(
                                emg_data[
                                    i * NUM_CHANNELS : (i * NUM_CHANNELS) + NUM_CHANNELS
                                ]
                            )

            except (ValueError, AttributeError) as e:
                print(repr(e))
                pass

    filename = str(filename + str(".mat"))

    spio.savemat(filename, {}, False)

    for key, value in m.items():
        try:
            with open(filename, "ab") as f:
                spio.savemat(
                    f,
                    {key: value},
                    appendmat=False,
                    long_field_names=True,
                    do_compression=True,
                    oned_as="row",
                )
        except (TypeError, IndexError) as e:
            print("Problem with key: " + key)
            print(repr(e))
            pass

    end_time = t.time()

    print("------ Parsed log in " + str(end_time - start_time) + " seconds ------")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        parse(sys.argv[1])
    else:
        print("Error - Usage: emg_log_parser.py <log_file_path>")

#!/usr/bin/env python
"""
Created on Tue Jan 26 2017

Python translation of CpchSerial.m in MATLAB minivie

@author: D. Samson
Updated 3-21-17 by Connor Pyles
"""
import struct

# Before usage, do the following:
#
# install pyserial: python -m pip install pyserial
#
# make sure any connections to COM object are closed, otherwise will get permission denied error

from scipy import signal  # Used for signal filtering
import numpy as np  # Used for buffer operations
import serial  # USB serial interface
import time
import threading
import logging
import h5py
from datetime import datetime
from inputs.cpc_headstage import CpcHeadstage
from inputs.signal_input import SignalInput


class CpchSerial(CpcHeadstage, SignalInput):
    """
    Class for interfacing CPCH via serial port
    
    This class is used to interface the JHU/APL Conventional Prosthetics Control Headstage (CPCH)
    via a USB-RS485 adaptor.  The adaptor is based on the FTDI chipset and drivers for the device 
    can be found here:  
    http://www.ftdichip.com/Drivers/VCP.htm
    Note the Virtual Com Port (VCP) drivers should be used (as opposed to the D2XX Direct Drivers)
    
    Typical Baud rate for the device is 921600 bps
    """

    def __init__(self, port='/dev/ttyUSB0', bioamp_mask=0xFFFF, gpi_mask=0xFFFF):
        """
        Inits CpchSerial with port information and channel selection parameters.
        :type port: str             # Port must be capable of 921600 baud
        :type bioamp_mask: int
        :type gpi_mask: int
        """
        # Initialize superclass
        super(CpchSerial, self).__init__()

        # Set up logging
        self.enable_data_logging = False  # Enables logging data stream to disk
        t = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._h5filename = t + '_CPCH_RAWBYTES.hdf5'
        self._h5file = None
        # self._h5file = h5py.File(self._h5filename, 'w')
        # self._h5file.close()
        self._rawbytes_log_counter = 1

        # Gain values from normalized values (Ref: RPP-700-ICD_-9959)
        self.gain_single_ended = 0.00489  # Range: 0-1023; .00489 Volts / Count; Range is [0, 5)
        self.gain_differential = 0.00489  # Range: -512 … 511; .00489 Volts / Count; Range is [-2.5, 2.5)

        # private set access variables
        self._count_total_messages = 0
        self._count_bad_length = 0
        self._count_bad_checksum = 0
        self._count_bad_status = 0
        self._count_bad_sequence = 0
        self._count_adc_error = 0

        # private access variables
        self._serial_obj = None
        self._data_buffer = []  # list of bytearrays
        self._serial_buffer = bytearray([])  # bytearray
        self._prev_data_frame_id = -1
        self._bioamp_cnt = 0
        self._gpi_cnt = 0
        self._start_time = time.perf_counter()
        self._is_running = False
        self.__valid_message_count = 0
        self.__valid_byte_count = 0
        self.__byte_count = 0
        self.__byte_available_count = 0
        self.__aligned_byte_count = 0
        self.__valid_message_rate = 0.0
        self.__valid_byte_rate = 0.0
        self.__byte_rate = 0.0
        self.__byte_available_rate = 0.0
        self.__aligned_byte_rate = 0.0
        self.__time_stream_reference = time.perf_counter()
        self.__stream_sleep_time = 0.02
        self._stream_duration = float("inf")

        # Initialize threading parameters
        self._stream_on_thread = True
        self.__lock = None
        self.__thread = None

        # public access variables
        self.serial_port = port  # Port must be capable of 921600 baud
        # bioamp_mask and gpi_mask parameters select which channels are requested to be streamed form the CPCH Device
        self.bioamp_mask = bioamp_mask
        self.gpi_mask = gpi_mask

        # Calculate channel mask (e.g. 0x00FF means channels 1-8, 0xFF00 means channels 7-16)
        # These channel mappings are updated based on the channel mask
        self.de_channel_idx = []
        for n in range(16):
            if self.bioamp_mask & (1 << n):
                self.de_channel_idx.append(n)
        self.se_channel_idx = []
        for n in range(16):
            if self.gpi_mask & (1 << n):
                self.se_channel_idx.append(n)

        # These do incorrect masking e.g. 0x00FF is first 8 channels (1-8) not (7-16) as below returns
        # self.de_channel_idx = [int(x) for x in '{0:016b}'.format(self.bioamp_mask)] + [0] * 16
        # self.de_channel_idx = [i for i, x in enumerate(self.de_channel_idx) if bool(x)]
        # self.se_channel_idx = [0] * 16 + [int(x) for x in '{0:016b}'.format(self.gpi_mask)]
        # self.se_channel_idx = [i for i, x in enumerate(self.se_channel_idx) if bool(x)]

        # channel_ids sub-selects the channel data buffer during get_data. That is, if 16 differential channels are
        # streaming, then channel_ids could be used to sub-select channels [1,3,5,7,15]
        self.num_channels = len(self.de_channel_idx) + len(self.se_channel_idx)
        self.channel_ids = list(range(self.num_channels))
        self.sample_frequency = 1000
        self.num_samples = 3000  # number of samples buffered for get_data. Can be changed before calling connect

    def connect(self):
        # Initialize the serial object

        self._bioamp_cnt = len(self.de_channel_idx)
        self._gpi_cnt = len(self.se_channel_idx)

        # buffer to hold collected data
        self._data_buffer = np.empty([self.num_samples, self.num_channels], dtype=np.double)

        if self.enable_data_logging:
            # moved from init() so files don't get written unless logging enabled
            self._h5file = h5py.File(self._h5filename, 'w')
            self._h5file.close()

        try:
            self._serial_obj = serial.Serial(
                port=self.serial_port,
                baudrate=921600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1.0,  # seconds
                xonxoff=False,  # disable software flow control
                rtscts=False,  # disable hardware (RTS/CTS) flow control
                dsrdtr=False,  # disable hardware (DSR/DTR) flow control
                writeTimeout=1,  # timeout for write
            )
            self._serial_obj.set_buffer_size(rx_size=2**16, tx_size=2**16)
            print(f'[{__file__}] CPCH Port Opened: {self.serial_port.upper()}')

        except Exception as exp:
            print(f'[{__file__}] CPCH Port FAILED')
            raise exp

        # Transmit STOP message in case data is flowing so the system can sanely start
        msg = self.encode_stop_msg()  # msg: bytearray(b'\x02\x9a')
        self._serial_obj.write(msg)

        while True:
            time.sleep(0.1)  # delay here to ensure all bytes have time for receipt
            bytes_available = self._serial_obj.in_waiting
            if bytes_available:
                self._serial_obj.read(bytes_available)
            else:
                break

        # Get CPCH ID
        # Read param to verify the message.  Note that this must be
        # read back to ensure the message structure is correct since
        # not all channels can (or will) return data.  Unrequested channels
        # are unreturned by the system.
        msg = self.encode_config_read_msg(self.param_id_cpch_id)
        self._serial_obj.write(msg)

        # Check response
        r = self._serial_obj.read(7)

        # Do this after the first read so that we can establish if any
        # response was given
        assert len(r) > 0, 'No response from CPCH. Check power, check connections'

        msg_id = self.msg_id_configuration_read_response
        assert len(r) == 7, f'Wrong number of bytes returned. Expected [7], received [{len(r)}]'
        assert r[0] == msg_id, f'Bad response message id.  Expected [{msg_id}], received [{r[0]}]'
        assert r[1] == self.param_id_cpch_id, f'Bad parameter id. Expected [1], received [{r[1]}]'
        assert not self.crc_func(r), 'Bad checksum'
        cpch_id = struct.unpack("<I", r[2:6])[0]  # unpack 4 bytes as little-endian unsigned int
        print(f'[{__file__}] CPCH Device ID = {cpch_id}')

        # Reconfigure the CPCH
        # msg example: [ 4    2  255  255    0    0  249]
        # 4 = write param
        # 2 = param type 2 (active channels)

        # Send Request
        channel_config = (self.gpi_mask << 16) + self.bioamp_mask
        msg = self.encode_config_write_msg(self.param_id_active_channels, channel_config)
        self._serial_obj.write(msg)

        # Check response
        r = self._serial_obj.read(3)

        msg_id = self.msg_id_configuration_write_response
        assert len(r) == 3, 'Wrong number of bytes returned'
        assert r[0] == msg_id, f'Bad response message id. Expected {msg_id}, got {r[0]}'
        assert not self.crc_func(r), 'Bad checksum'
        assert r[1] == self.config_write_success, 'Configuration Write Failed'

        # Read back param to verify the message.  Note that this must be
        # read back to ensure the message structure is correct since
        # not all channels can (or will) return data.  Unrequested channels
        # are unreturned by the system.
        msg = self.encode_config_read_msg(self.param_id_active_channels)
        self._serial_obj.write(msg)

        # Check response
        r = self._serial_obj.read(7)

        assert len(r) == 7, 'Wrong number of bytes returned'
        assert r[0] == self.msg_id_configuration_read_response, 'Bad response message id'
        assert not self.crc_func(r), 'Bad checksum'
        assert r[1] == self.param_id_active_channels, 'Bad config parameter id'
        channel_config_response = struct.unpack("<I", r[2:6])[0]  # unpack 4 bytes as little-endian unsigned int
        assert channel_config_response == channel_config, f'Defined channel mask does not match returned mask. ' \
                                                          f'Expected: uint32[{channel_config}] '\
                                                          f'Got: uint32[{channel_config_response}] '

    def start(self):
        # Start the data streaming

        self._start_time = time.perf_counter()
        print('[%s] Starting CPCH with %d differential and %d single-ended inputs...' % (
            __file__, self._bioamp_cnt, self._gpi_cnt))

        if self._serial_obj.closed:
            self._serial_obj.open()

        if not self._serial_obj.closed:
            msg = self.encode_start_msg()

            bytes_available = self._serial_obj.in_waiting
            if bytes_available:
                self._serial_obj.read(bytes_available)

            self._serial_obj.write(msg)
            self._is_running = True

        if self._stream_on_thread:
            # Create thread-safe lock so that user based reading of values and thread-based
            # writing of values do not conflict
            self.__lock = threading.Lock()

            # Create a thread for processing new incoming data
            self.__thread = threading.Thread(target=self._stream_data)
            self.__thread.name = 'CPCHSerial'
            self.__thread.start()
        else:
            # Run without thread, mainly for profiling purposes
            self.__lock = None
            self._stream_data()

    def get_data(self, num_samples=None, idx_channel=None):
        # Return data from internal buffer

        num_samples = num_samples or self.num_samples
        idx_channel = idx_channel or self.channel_ids

        # Start device if not already running
        if self._serial_obj.closed or not self._is_running:
            self.start()

        # Return data from buffer
        data = self._data_buffer[-num_samples:, idx_channel]

        # Filter data
        # Inputs.HighPass(20,3,Fs)
        # 20 Hz break freq, 3rd order 1000Hz
        sos = signal.butter(3, 20, btype='highpass', output='sos', fs=1000)
        filtered = signal.sosfiltfilt(sos, data, axis=0)

        return filtered

    def _stream_data(self):
        # Loop to receive data.  This function runs on the target thread
        start_time = time.perf_counter()
        while (time.perf_counter()- start_time) < self._stream_duration:
            # Every 20 ms should be roughly 20 messages
            time.sleep(self.__stream_sleep_time)

            # Check for new data
            num_available = self._serial_obj.in_waiting

            if num_available == 0:
                # print('No data available from serial buffer, internal buffer not updated.')
                pass
            else:
                if self._stream_on_thread:
                    with self.__lock:
                        self._read_serial_buffer()
                else:
                    self._read_serial_buffer()

    def _read_serial_buffer(self):
        # Record start time of this loop
        stream_loop_start_time = time.perf_counter()

        # Read samples from serial buffer and place in internal buffer
        # (potentially with leftover remaining bytes)
        num_available = self._serial_obj.in_waiting
        # print(f'Num Serial Bytes Waiting: {num_available}')
        r = bytearray(self._serial_obj.read(num_available))
        raw_bytes = self._serial_buffer + r

        payload_size = 2 * (self._bioamp_cnt + self._gpi_cnt)
        msg_size = payload_size + 6

        # Align the data bytes. If all's well the first byte of the
        # remainder should be a start char which is saved for the next
        # time the buffer is read
        d = self.align_data_bytes(raw_bytes, msg_size)
        aligned_data = d['data_aligned']
        remainder_bytes = d['remainder_bytes']

        num_aligned_bytes = sum([len(x) for x in aligned_data])
        num_remainder_bytes = len(remainder_bytes)
        # DEBUG
        # print('Byte Align Fast Debug:')
        # print('Num Bytes In: ' + str(len(raw_bytes)))
        # print('Num Aligned Bytes Out: ' + str(num_aligned_bytes))
        # print('Num Remainder Bytes Out: ' + str(num_remainder_bytes))
        # print('Num Total Bytes Out: ' + str(num_aligned_bytes + num_remainder_bytes))

        # Store remaining bytes for the next read
        self._serial_buffer = remainder_bytes

        # No new data
        if not aligned_data:
            print('No aligned data available from CPC serial buffer, internal buffer not updated.')
            self._set_stream_sleep_time(stream_loop_start_time, 0.02)
            return

        # Check validation parameters(chksum, etc)
        d = self.validate_messages(aligned_data, payload_size)
        if (d is None) or ('valid_data' not in d.keys()):  # Sometimes this is empty
            print('No valid data available from CPC serial buffer, internal buffer not updated.')
            self._set_stream_sleep_time(stream_loop_start_time, 0.02)
            return

        valid_data = d['valid_data']
        error_stats = d['error_stats']

        self._count_total_messages += len(aligned_data)
        self._count_bad_checksum += error_stats['sum_bad_checksum']
        self._count_bad_status += error_stats['sum_bad_status']
        self._count_bad_sequence += error_stats['sum_bad_sequence']
        self._count_adc_error += error_stats['sum_adc_error']

        num_valid_samples = len(valid_data)
        num_valid_bytes_per_message = [len(x) for x in valid_data]
        num_valid_bytes = sum(num_valid_bytes_per_message)
        num_aligned_bytes = sum([len(x) for x in aligned_data])
        num_bytes = len(raw_bytes)

        assert num_valid_bytes_per_message == [msg_size] * len(num_valid_bytes_per_message)

        # Extract the signals
        d = self.get_signal_data(valid_data, self._bioamp_cnt, self._gpi_cnt)
        diff_data_i16 = d['diff_data_int16']
        se_data_u16 = d['se_data_u16']

        # Perform scaling
        # Convert to numpy ndarrays
        de_data_normalized = np.array(diff_data_i16, dtype='float') * self.gain_differential
        se_data_normalized = np.array(se_data_u16, dtype='float') / 1024.0 * self.gain_single_ended

        # Log data
        self._log_data(raw_bytes)

        if num_valid_samples > self._data_buffer.shape[0]:
            # Replace entire buffer
            if any(self.de_channel_idx):
                self._data_buffer[:, self.de_channel_idx] = de_data_normalized[-self._data_buffer.shape[0]:,
                                                            self.de_channel_idx]
            if any(self.se_channel_idx):
                self._data_buffer[:, self.se_channel_idx] = se_data_normalized[-self._data_buffer.shape[0]:,
                                                            self.se_channel_idx]
        else:
            # Check for buffer overrun
            self._data_buffer = np.roll(self._data_buffer, -num_valid_samples, axis=0)
            buffer_sample_idx = range(self._data_buffer.shape[0] - num_valid_samples, self._data_buffer.shape[0])
            for i, buffer_channel_idx in enumerate(self.de_channel_idx):
                self._data_buffer[buffer_sample_idx, buffer_channel_idx] = de_data_normalized[:, i]
            for i, buffer_channel_idx in enumerate(self.se_channel_idx):
                self._data_buffer[buffer_sample_idx, buffer_channel_idx] = se_data_normalized[:, i]

        # Compute data rate
        if self.__valid_message_count == 0:
            # mark time
            # Need to account for sleep time prior to start_time measured
            self.__time_stream_reference = stream_loop_start_time - self.__stream_sleep_time
        self.__valid_message_count += num_valid_samples
        self.__valid_byte_count += num_valid_bytes
        self.__byte_count += num_bytes
        self.__byte_available_count += num_available
        self.__aligned_byte_count += num_aligned_bytes

        t_now = time.perf_counter()
        t_elapsed = t_now - self.__time_stream_reference

        if t_elapsed > 5.0:
            # compute rate (every second)
            self.__valid_message_rate = self.__valid_message_count / t_elapsed
            self.__valid_byte_rate = self.__valid_byte_count / t_elapsed
            self.__byte_rate = self.__byte_count / t_elapsed
            self.__byte_available_rate = self.__byte_available_count / t_elapsed
            self.__aligned_byte_rate = self.__aligned_byte_count / t_elapsed

            self.__valid_message_count = 0
            self.__valid_byte_count = 0
            self.__byte_count = 0
            self.__byte_available_count = 0
            self.__aligned_byte_count = 0

            s = 'CPC Valid Message Rate: {0:.2f} kHz, (Expected:  1.00 kHz)'.format(self.__valid_message_rate / 1000.0)
            # print(s)
            logging.info(s)

        # Update sleep time
        self._set_stream_sleep_time(stream_loop_start_time, 0.02)

    def get_status_msg(self):
        # return string formatted status message
        # with data rate and battery percentage
        # E.g. 1000Hz
        return f'CPCH: {self.__valid_message_rate:.0f}Hz {self.__byte_rate/1000*8:.1f}kbps'

    def _set_stream_sleep_time(self, stream_loop_start_time, target_dt):
        # Update loop sleep time to account for processing time
        stream_loop_time_elapsed = time.perf_counter() - stream_loop_start_time
        if stream_loop_time_elapsed < target_dt:
            self.__stream_sleep_time = target_dt - stream_loop_time_elapsed
        else:
            self.__stream_sleep_time = 0.0
            rate = 1.0 / target_dt
            logging.info('CPC Running Behind {0:.2f} Hz'.format(rate))

    def _log_data(self, raw_bytes):
        # Method to log all raw bytes as hdf5
        # Should append to file each time
        if self.enable_data_logging:
            self._h5file = h5py.File(self._h5filename, 'r+')
            t = datetime.now()
            g1 = self._h5file.create_group('ByteRead_{0:05d}'.format(self._rawbytes_log_counter))
            g1.create_dataset('rawbytes', data=[x for x in raw_bytes], shape=(len(raw_bytes), 1), dtype='uint8')
            encoded = [a.encode('utf8') for a in str(t)]  # Need to encode strings
            g1.create_dataset('timestamp', data=encoded, shape=(len(encoded), 1))
            self._rawbytes_log_counter += 1
            self._h5file.close()

    def close(self):
        # Method to disconnect object
        logging.info("Closing CPC Serial comms {}".format(self.serial_port))
        self._serial_obj.close()

    def stop(self):
        self.close()


def run_stream_profile():
    # Method to run profile on data streaming to determine slowest function calls
    import cProfile

    # Initialize object
    obj = CpchSerial()
    obj.enable_data_logging = True
    # Remove threading to allow for profiling
    obj._stream_on_thread = False
    # Set stream duration to make sure it stops streaming
    obj._stream_duration = 1.0

    # Connect
    obj.connect()

    # Run profiler
    sort_mode = 'cumulative'
    cProfile.runctx('obj.start()', globals(), locals(), 'cpc_profile')

    # Can view "snakeviz signal_viewer_profile" from terminal
    # snakeviz profile_name


def main():
    import argparse

    # Parameters:
    parser = argparse.ArgumentParser(description='CPCH: Read from CPCH and log.')
    parser.add_argument('-p', '--PORT', help='Serial Port Name (e.g. /dev/ttyUSB0)',
                        default='/dev/ttyUSB0')
    args = parser.parse_args()

    # Logging
    f = 'cpch-' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.log'
    logging.basicConfig(filename=f, level=logging.DEBUG, format='%(asctime)s %(message)s')

    # Initialize object
    obj = CpchSerial(port=args.PORT)
    obj.enable_data_logging = True
    # Connect and start streaming
    obj.connect()
    obj.start()

    # for i in range(50):
    #     time.sleep(0.1)
    #     d = obj.get_data()
    #     print('New Data')
    #     print(d)


if __name__ == '__main__':
    main()

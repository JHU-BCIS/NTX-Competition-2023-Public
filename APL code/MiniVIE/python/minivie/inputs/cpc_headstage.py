"""
Created on Tue Jan 26 2017

Python translation of CpcHeadstage.m in MATLAB minivie

@author: D. Samson
Updated 3-21-17 by Connor Pyles
Updated 10-9-22 by R. Armiger to use python CRC, fix errors and test with CPCH decoding
"""
import struct
import crcmod
import numpy as np


class CpcHeadstage(object):
    """
    # Base class for CPCH
    # Contains methods for creating and parsing messages
    # as well as parsing streaming data
    # 14Mar2012 Armiger: Created
    # 15Jan2013 Armiger: Updated signal parsing to search for only start
    # characters ('128') since start sequence [128 0 0] cannot be relied
    # upon if transmission errors occur
    """

    def __init__(self):

        # CPCH Message IDs
        self.msg_id_start_streaming = 1
        self.msg_id_stop_streaming = 2
        self.msg_id_status_request = 3
        self.msg_id_configuration_write = 4
        self.msg_id_configuration_read = 5
        self.msg_id_cpc_data = 128
        self.msg_id_stop_streaming_response = 129
        self.msg_id_status_data = 130
        self.msg_id_configuration_read_response = 131
        self.msg_id_configuration_write_response = 132

        # CPCH Parameters (used for configuration read/write)
        self.param_id_reserved = 0
        self.param_id_cpch_id = 1
        self.param_id_active_channels = 2

        # Configuration Write Response
        self.config_write_success = 1

        # Use crcmod utilities for efficient CRC checking
        # crc_func modified via lambda function to return a single byte instead of int
        self.crc_func = crcmod.mkCrcFun(int('101001101', 2), initCrc=0, rev=False)

        # pre-generate the crc table for fast xor checking
        self.crc_table = [self.crc_func(struct.pack('B', i)) for i in range(256)]

    def encode_start_msg(self):
        msg = struct.pack('B', self.msg_id_start_streaming)
        crc = struct.pack('B', self.crc_func(msg))
        return msg + crc

    def encode_stop_msg(self):
        msg = struct.pack('B', self.msg_id_stop_streaming)
        crc = struct.pack('B', self.crc_func(msg))
        return msg + crc

    def encode_status_msg(self):
        msg = struct.pack('B', self.msg_id_status_request)
        crc = struct.pack('B', self.crc_func(msg))
        return msg + crc

    def encode_config_read_msg(self, param_id):
        msg = struct.pack('BB', self.msg_id_configuration_read, param_id)
        crc = struct.pack('B', self.crc_func(msg))
        return msg + crc

    def encode_config_write_msg(self, param_id, payload):
        # payload is Uint32Type
        msg = struct.pack('<BBI', self.msg_id_configuration_write, param_id, payload)
        crc = struct.pack('B', self.crc_func(msg))
        return msg + crc

    def crc_validate(self, msg_in):
        """
        XOR checksum of msg

        Input Arguments:
        msg -- list of bytearrays to be checksummed

        Return Arguments:
        crc_result -- ndarray with 0 when good checksum for each message

        Modified 3/15/17 by COP to handle lists of messages
        """
        num_messages, num_bytes = msg_in.shape

        crc_result = np.zeros(num_messages, dtype=np.uint8) # initialize crc result
        for byte_idx in range(num_bytes):
            xor_result = np.bitwise_xor(crc_result, msg_in[:, byte_idx])
            crc_result[:] = [self.crc_table[x] for x in xor_result]

        return crc_result

    def align_data_bytes(self, data_stream, msg_size):
        d = self.byte_align_fast(data_stream, msg_size)
        return d

    @staticmethod
    def byte_align_fast(data_stream, msg_size):

        # Find all start chars ('128') and index the next set of bytes
        # off of these starts.  This could lead to overlapping data
        # but valid data will be verified using the checksum
        byte_pattern = [128, 0, 0]
        idx_start_bytes = [i for i, x in enumerate(data_stream) if x == 128]

        if not idx_start_bytes:
            print('No start sequence [' + ' '.join(
                str(x) for x in byte_pattern) + '] found in data stream of length %d.  Try resetting CPCH' % (
                      len(data_stream)))

        # Check if there are too few bytes between the last start
        # character and the end of the buffer
        idx_start_bytes_in_range = [x for x in idx_start_bytes if x <= len(data_stream) - msg_size]
        if not idx_start_bytes_in_range:
            # No full messages found
            d = {'data_aligned': [], 'remainder_bytes': data_stream}
            return d

        # Check start bytes to make sure they are separated by correct message size
        check_msg_sizes = True
        while check_msg_sizes:
            for i, this_start_idx in enumerate(idx_start_bytes_in_range):
                if i == len(idx_start_bytes_in_range) - 1:
                    check_msg_sizes = False  # All msg sizes checked
                    continue
                if not (idx_start_bytes_in_range[i + 1] - this_start_idx) == msg_size:
                    del idx_start_bytes_in_range[i + 1]
                    break  # break for loop to re-enter again now that start byte list has been modified

        remainder_bytes = data_stream[idx_start_bytes_in_range[-1] + msg_size:]

        # Align the data based on the validated start characters
        data_aligned = []
        for i in idx_start_bytes_in_range:
            data_aligned.append(data_stream[i: i + msg_size])

        # Return data
        d = {'data_aligned': data_aligned, 'remainder_bytes': remainder_bytes}
        return d

    def validate_messages(self, aligned_msg, expected_length):
        """
        Validate a matrix of messages using a criteria of checksum,
        appropriate message length, and status bytes

        Aligned data should be a list of length = numMessages,
        with each element being bytearray of length = numBytesPerMessage
        """
        # Convert input to ndarray to speed things up
        aligned_data = np.array(aligned_msg, dtype=np.uint8)

        # Compute CRC
        # t = time.time()
        # 0.0009133815765380859 sec
        # ndarray: 56,0
        is_valid_checksum = self.crc_validate(aligned_data) == 0
        # elapsed = time.time() - t
        # print(elapsed)

        # Find validated data by ensuring it is the correct length and has correct checksum
        # Status byte upper four bits are set to zero
        # /* if the bit is set to 1, this indicates error within the last transmitted sample */
        #	BoolType		message_id_error:1;
        #	BoolType		cmd_msg_checksum_error:1;
        #	BoolType		cmd_msg_length_error:1;
        #	BoolType		ADC_error:1;

        # check for any high bits in upper region:
        is_valid_status_byte = aligned_data[:, 2] & 0xf0 == False
        is_not_adc_error = (aligned_data[:, 2] & 0x08) == False
        is_valid_length = aligned_data[:, 4] == expected_length

        # remove samples with any invalid elements
        # RSA: 10/9/2022 got a few instances where ADC error when high.  we will still accept samples
        # valid_data = aligned_data[is_valid_status_byte & is_not_adc_error & is_valid_length, :]
        valid_data = aligned_data[is_valid_status_byte & is_valid_length, :]
        num_valid = valid_data.shape[0]

        sum_bad_status = np.size(is_valid_status_byte) - np.count_nonzero(is_valid_status_byte)
        sum_bad_length = np.size(is_valid_length) - np.count_nonzero(is_valid_length)
        sum_bad_checksum = np.size(is_valid_checksum) - np.count_nonzero(is_valid_checksum)
        # sum_bad_sequence = np.size(is_valid_sequence) - np.count_nonzero(is_valid_sequence)
        sum_adc_error = np.size(is_not_adc_error) - np.count_nonzero(is_not_adc_error)

        error_stats = {'sum_bad_status': sum_bad_status, 'sum_bad_length': sum_bad_length,
                       'sum_bad_checksum': sum_bad_checksum, 'sum_bad_sequence': 0,
                       'sum_adc_error': sum_adc_error}

        if not num_valid:
            # No valid data in packet
            print(f'Num BAD ADC {sum_adc_error}')
            print(error_stats)
            return

        # Check sequence bytes in batch operation
        sequence_row = valid_data[:, 3]
        sequence_expected = np.arange(sequence_row[0], sequence_row[0] + num_valid, dtype=np.uint8)
        is_valid_sequence = sequence_expected == sequence_row
        sum_bad_sequence = np.size(is_valid_sequence) - np.count_nonzero(is_valid_sequence)

        error_stats = {'sum_bad_status': sum_bad_status, 'sum_bad_length': sum_bad_length,
                       'sum_bad_checksum': sum_bad_checksum, 'sum_bad_sequence': sum_bad_sequence,
                       'sum_adc_error': sum_adc_error}
        d = {'valid_data': valid_data, 'error_stats': error_stats}
        return d

    @staticmethod
    def get_signal_data(valid_data, diff_cnt, se_cnt):
        # Typecast the data to the appropriate data size

        # Get data size
        num_valid_samples = len(valid_data)

        if diff_cnt > 0:

            # Convert the valid data to Int16int
            payload_idx_start = 5
            payload_idx_end = payload_idx_start + 2 * diff_cnt  # Diff data starts after header
            de_data_u8 = [x[payload_idx_start:payload_idx_end] for x in valid_data]
            string_num_int16 = str(int((payload_idx_end - payload_idx_start) / 2))

            diff_data_int16 = []
            for x in de_data_u8:
                # print('DE Message: ' + str(x))
                new_val = struct.unpack(string_num_int16 + 'h', x)
                # print('DE Converted: ' + str(new_val))
                diff_data_int16.append(new_val)
        else:
            diff_data_int16 = None

        if se_cnt > 0:
            payload_idx_start = 5 + 2 * diff_cnt  # se data starts after diff data
            payload_idx_end = payload_idx_start + 2 * se_cnt

            se_data_u8 = [x[payload_idx_start:payload_idx_end] for x in valid_data]
            string_num_uint16 = str(int((payload_idx_end - payload_idx_start) / 2))
            # se_data_u16 = [struct.unpack(string_num_uint16 + 'H', x) for x in se_data_u8]
            se_data_u16 = []
            for x in se_data_u8:
                # print('SE Message: ' + str(x))
                new_val = struct.unpack(string_num_uint16 + 'H', x)
                # print('SE Converted: ' + str(new_val))
                se_data_u16.append(new_val)
        else:
            se_data_u16 = None

        d = {'diff_data_int16': diff_data_int16, 'se_data_u16': se_data_u16}
        return d

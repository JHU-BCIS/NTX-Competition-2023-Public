% MyoBtle - MiniVIE SignalSource for myo band via direct btle comms
% This class will establish a myo armband connection via MATLAB btle
% and follows the interface given by Inputs.SignalInput
%
% Myo Protocol specification here:
% https://developerblog.myo.com/myo-bluetooth-spec-released/
% See also: myohw.h
%
% Usage:
%   myo = Inputs.MyoBtle();
%   myo.initialize('MACADDRESS')
%   plot(myo.getData)
%   myo.close()
%
%
% Notes:
%   If input argument isn't provided on 'initialize', then this will read  
%   the xml config variable: myoBtleDeviceName
%   Use MATLAB's 'blelist' to specify the device by 'Name' or 'Address'
% 
% TODO:
%   - Add IMU Support
%   - Add second myo support
%
% Revisions:
%   03AUG2022 Armiger: Created
%
classdef MyoBtle < Inputs.SignalInput
    properties
        EMG_GAIN = 0.01;  %Scaling from int8 to voltage
    end
    properties (SetAccess = private)
        hMyoBtle
        DataBuffer
        EmgData0Characteristic
        EmgData1Characteristic
        EmgData2Characteristic
        EmgData3Characteristic
    end
    methods
        function initialize(obj, dev_name)
            %
            % Establish myo armband connection via MATLAB btle
            %
            if nargin < 2
                MAC = UserConfig.getUserConfigVar('myoBtleDeviceName','Myo');
            else
                MAC = dev_name;
            end

            obj.SampleFrequency = 200; % Hz
            obj.ChannelIds = 1:8;
            obj.NumSamples = 1000;
            obj.Verbose = 1;
            obj.DataBuffer = zeros(obj.NumChannels,5000);

            fprintf('Connecting to %s:\n', MAC);
            myo = ble(MAC);
            obj.hMyoBtle = myo;

            fprintf('---------------------------------\n')
            fprintf('Reading Named Characteristics:\n')
            fprintf('---------------------------------\n')

            vals = read(characteristic(myo, 'Generic Access', 'Device Name'));
            fprintf('Device Name: %s\n',char(vals))

            vals = read(characteristic(myo, 'Generic Access', 'Appearance'));
            fprintf('Appearance: 0x%02x 0x%02x\n',vals)

            vals = read(characteristic(myo, 'Generic Access', 'Peripheral Preferred Connection Parameters'));
            fprintf('Peripheral Preferred Connection Parameters: 0x%02x 0x%02x 0x%02x 0x%02x 0x%02x 0x%02x 0x%02x 0x%02x\n',vals)

            vals = read(characteristic(myo, 'Device Information', 'Manufacturer Name String'));
            fprintf('Manufacturer Name String: %s\n',char(vals))

            vals = read(characteristic(myo, 'Battery Service', 'Battery Level'));
            fprintf('Battery Level: %d%%\n',vals)


            % MyoInfoCharacteristic (0x0101)
            fprintf('---------------------------------\n')
            fprintf('Reading MyoInfoCharacteristic (0x0101):\n')
            fprintf('---------------------------------\n')

            vals = read(characteristic(myo, 'D5060001-A904-DEB9-4748-2C7F4A124842', 'D5060101-A904-DEB9-4748-2C7F4A124842'));

            % serial_number[6]
            fprintf('serial_number: %x%x%x%x%x%x\n',fliplr(uint8(vals(1:6))))

            % unlock_pose
            switch typecast(uint8(vals(7:8)),'uint16') %myohw_pose_t
                case 0
                    unlock_pose = 'rest';
                case 1
                    unlock_pose = 'fist';
                case 2
                    unlock_pose = 'wave_in';
                case 3
                    unlock_pose = 'wave_out';
                case 4
                    unlock_pose = 'finger_spread';
                case 5
                    unlock_pose = 'double_tap';
                case hex2dec('ffff')
                    unlock_pose = 'unknown';
                otherwise
                    unlock_pose = 'invalid';
            end
            fprintf('unlock_pose: %s\n', unlock_pose)

            % active_classifier_type
            switch vals(9) %myohw_classifier_model_type_t
                case 0
                    active_classifier_type = 'Model built into the classifier package';
                case 1
                    active_classifier_type = 'Model based on personalized user data';
                otherwise
                    active_classifier_type = 'invalid';
            end
            fprintf('active_classifier_type: %s\n', active_classifier_type)
            fprintf('active_classifier_index: %d\n', vals(10))
            fprintf('has_custom_classifier: %d\n', vals(11))
            fprintf('stream_indicating: %d\n', vals(12))
            switch vals(13) %myohw_sku_t
                case 0
                    myohw_sku = 'Unknown SKU (default value for old firmwares)';
                case 1
                    myohw_sku = 'Black Myo';
                case 2
                    myohw_sku = 'White Myo';
                otherwise
                    myohw_sku = 'invalid';
            end
            fprintf('sku: %s\n', myohw_sku)


            % FirmwareVersionCharacteristic (0x0201)
            fprintf('---------------------------------\n')
            fprintf('Reading FirmwareVersionCharacteristic (0x0201):\n')
            fprintf('---------------------------------\n')

            vals = read(characteristic(myo, 'D5060001-A904-DEB9-4748-2C7F4A124842', 'D5060201-A904-DEB9-4748-2C7F4A124842'));
            converted = typecast(uint8(vals),'uint16');
            switch converted(4) % myohw_hardware_rev_t
                case 0
                    hw_rev = 'unknown';
                case 1
                    hw_rev = 'Myo Alpha (REV-C) hardware';
                case 2
                    hw_rev = 'Myo (REV-D) hardware';
                otherwise
                    hw_rev = 'unknown';
            end
            fprintf('FirmwareVersionCharacteristic: Major: %d Minor: %d Patch: %d HardwareRev: %d (%s)\n', converted, hw_rev)


            % CommandCharacteristic (0x0401) myohw_command_t
            fprintf('---------------------------------\n')
            fprintf('Sending CommandCharacteristic (0x0401):\n')
            fprintf('---------------------------------\n')

            CommandCharacteristic = characteristic(myo, 'D5060001-A904-DEB9-4748-2C7F4A124842', 'D5060401-A904-DEB9-4748-2C7F4A124842');
            myohw_command_set_mode               = 01; % < Set EMG and IMU modes. See myohw_command_set_mode_t.
            myohw_command_vibrate                = 03; % < Vibrate. See myohw_command_vibrate_t.
            myohw_command_deep_sleep             = 04; % < Put Myo into deep sleep. See myohw_command_deep_sleep_t.
            myohw_command_vibrate2               = 07; % < Extended vibrate. See myohw_command_vibrate2_t.
            myohw_command_set_sleep_mode         = 09; % < Set sleep mode. See myohw_command_set_sleep_mode_t.
            myohw_command_unlock                 = 10; % < Unlock Myo. See myohw_command_unlock_t.
            myohw_command_user_action            = 11; % < Notify user that an action has been recognized / confirmed.

            fprintf('Sleep Mode: Never\n')
            myohw_sleep_mode_normal      = 0; % < Normal sleep mode; Myo will sleep after a period of inactivity.
            myohw_sleep_mode_never_sleep = 1; % < Never go to sleep.
            write(CommandCharacteristic,[myohw_command_set_sleep_mode 1 myohw_sleep_mode_never_sleep])

            fprintf('Set EMG and IMU modes: \n')
            % EMG modes.
            myohw_emg_mode_none         = 0; % < Do not send EMG data.
            myohw_emg_mode_send_emg     = 2; % < Send filtered EMG data.
            myohw_emg_mode_send_emg_raw = 3; % < Send raw (unfiltered) EMG data.

            % IMU modes.
            myohw_imu_mode_none        = 0; % < Do not send IMU data or events.
            myohw_imu_mode_send_data   = 1; % < Send IMU data streams (accelerometer, gyroscope, and orientation).
            myohw_imu_mode_send_events = 2; % < Send motion events detected by the IMU (e.g. taps).
            myohw_imu_mode_send_all    = 3; % < Send both IMU data streams and motion events.
            myohw_imu_mode_send_raw    = 4; % < Send raw IMU data streams.

            % Classifier modes.
            myohw_classifier_mode_disabled = 0; % < Disable and reset the internal state of the onboard classifier.
            myohw_classifier_mode_enabled  = 1; % < Send classifier events (poses and arm events).

            fprintf('RAW EMG and IMU\n')
            emg_mode = myohw_emg_mode_send_emg_raw;
            imu_mode = myohw_imu_mode_send_data;
            classifier_mode = myohw_classifier_mode_disabled;

            write(CommandCharacteristic,[myohw_command_set_mode 3 emg_mode imu_mode classifier_mode])

            obj.EmgData0Characteristic = characteristic(myo, 'D5060005-A904-DEB9-4748-2C7F4A124842', 'D5060105-A904-DEB9-4748-2C7F4A124842');
            obj.EmgData1Characteristic = characteristic(myo, 'D5060005-A904-DEB9-4748-2C7F4A124842', 'D5060205-A904-DEB9-4748-2C7F4A124842');
            obj.EmgData2Characteristic = characteristic(myo, 'D5060005-A904-DEB9-4748-2C7F4A124842', 'D5060305-A904-DEB9-4748-2C7F4A124842');
            obj.EmgData3Characteristic = characteristic(myo, 'D5060005-A904-DEB9-4748-2C7F4A124842', 'D5060405-A904-DEB9-4748-2C7F4A124842');

            obj.EmgData0Characteristic.DataAvailableFcn = @(src,evt) obj.data_callback(src,evt);
            obj.EmgData1Characteristic.DataAvailableFcn = @(src,evt) obj.data_callback(src,evt);
            obj.EmgData2Characteristic.DataAvailableFcn = @(src,evt) obj.data_callback(src,evt);
            obj.EmgData3Characteristic.DataAvailableFcn = @(src,evt) obj.data_callback(src,evt);

            subscribe(obj.EmgData0Characteristic,'notification')
            subscribe(obj.EmgData1Characteristic,'notification')
            subscribe(obj.EmgData2Characteristic,'notification')
            subscribe(obj.EmgData3Characteristic,'notification')

        end
        function data = getData(obj,numSamples,idxChannel)
            %data = getData(obj,numSamples,idxChannel)
            % get data from buffer.  most recent sample will be at (end)
            % position.
            % DataBuffer = [NumSamples by NumChannels];
            %
            % optional arguments:
            %   numSamples, the number of samples requested from getData
            %   idxChannel, an index into the desired channels.  E.g. get the
            %   first four channels with iChannel = 1:4

            if nargin < 2
                numSamples = obj.NumSamples;
            end

            if nargin < 3
                idxChannel = 1:obj.NumChannels;
            end

            dataBuff = obj.DataBuffer(:,end-numSamples+1:end)';

            data = obj.EMG_GAIN .* double(dataBuff(:,idxChannel));

        end
        function data_callback(obj, src, evt)

            %   Characteristic with properties:
            %
            %              Name: "Custom"
            %              UUID: "D5060305-A904-DEB9-4748-2C7F4A124842"
            %        Attributes: "Notify"
            %       Descriptors: [1x3 table]
            %  DataAvailableFcn: @(src,evt)obj.data_callback(src,evt)
            %
            % Show descriptors
            %

            % Use 'oldest' inside the DataAvailableFcn callback function to avoid errors caused by the flushing of previous data.
            new_vals = double(typecast(uint8(read(src,'oldest')),'int8'));
            numNewSamples = 2;
            numChannels = 8;
            obj.DataBuffer = circshift(obj.DataBuffer,[0 -numNewSamples]);
            obj.DataBuffer(1:numChannels,end-1) = new_vals(1:8)';
            obj.DataBuffer(1:numChannels,end) = new_vals(9:16)';

        end
        function isReady = isReady(obj,numSamples)
            isReady = True;
        end
        function start(obj)
        end
        function stop(obj)
        end
        function deep_sleep(obj)
            % Send Myo into deep sleep (requires USB connection to wake)
            fprintf('Deep Sleep\n')
            CommandCharacteristic = characteristic(obj.hMyoBtle, 'D5060001-A904-DEB9-4748-2C7F4A124842', 'D5060401-A904-DEB9-4748-2C7F4A124842');
            myohw_command_deep_sleep             = 04; % < Put Myo into deep sleep. See myohw_command_deep_sleep_t.
            % write(CommandCharacteristic,[myohw_command_deep_sleep 0],"withoutresponse")
            try
                write(CommandCharacteristic,[myohw_command_deep_sleep 0])
            catch ME
                switch ME.identifier
                    case 'MATLAB:ble:ble:failToWriteCharacteristic'
                        fprintf('Device Disconnected\n')
                    otherwise
                        rethrow(ME)
                end
            end
        end
        function close(obj)
            fprintf('Closing BTLE interface...')
            unsubscribe(obj.EmgData0Characteristic)
            unsubscribe(obj.EmgData1Characteristic)
            unsubscribe(obj.EmgData2Characteristic)
            unsubscribe(obj.EmgData3Characteristic)
            obj.EmgData0Characteristic.DataAvailableFcn = [];
            obj.EmgData1Characteristic.DataAvailableFcn = [];
            obj.EmgData2Characteristic.DataAvailableFcn = [];
            obj.EmgData3Characteristic.DataAvailableFcn = [];
            obj.hMyoBtle = [];  % this will break the ble connection as intended
            fprintf('Done\n')
        end
    end
end

%
% Demo to walk through myo armband connection via MATLAB btle connection
%
% Protocol specification here: 
% https://developerblog.myo.com/myo-bluetooth-spec-released/
% See also: myohw.h
%
% Revisions:
%   03AUG2022 Armiger: Created
%

clear all % clear btle connections

fprintf('Listing BLE Devices:\n');
blelist

MAC = 'C30AEA1414D9'
% MAC = 'E8A2460B2C49';
% MAC = 'D85380BA2EBE';
fprintf('Connecting to %s:\n', MAC);
myo = ble(MAC);

%myo.Characteristics:
%         ServiceName                      ServiceUUID                               CharacteristicName                           CharacteristicUUID                    Attributes      
%     ____________________    ______________________________________    ____________________________________________    ______________________________________    ______________________
% 
%     "Generic Access"        "1800"                                    "Device Name"                                   "2A00"                                    {["Read"    "Write" ]}
%     "Generic Access"        "1800"                                    "Appearance"                                    "2A01"                                    {["Read"            ]}
%     "Generic Access"        "1800"                                    "Peripheral Preferred Connection Parameters"    "2A04"                                    {["Read"            ]}
%     "Generic Attribute"     "1801"                                    "Service Changed"                               "2A05"                                    {["Indicate"        ]}
%     "Device Information"    "180A"                                    "Manufacturer Name String"                      "2A29"                                    {["Read"            ]}
%     "Battery Service"       "180F"                                    "Battery Level"                                 "2A19"                                    {["Read"    "Notify"]}
%     "Custom"                "D5060001-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060101-A904-DEB9-4748-2C7F4A124842"    {["Read"            ]}
%     "Custom"                "D5060001-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060201-A904-DEB9-4748-2C7F4A124842"    {["Read"            ]}
%     "Custom"                "D5060001-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060401-A904-DEB9-4748-2C7F4A124842"    {["Write"           ]}
%     "Custom"                "D5060002-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060402-A904-DEB9-4748-2C7F4A124842"    {["Notify"          ]}
%     "Custom"                "D5060002-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060502-A904-DEB9-4748-2C7F4A124842"    {["Indicate"        ]}
%     "Custom"                "D5060003-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060103-A904-DEB9-4748-2C7F4A124842"    {["Indicate"        ]}
%     "Custom"                "D5060004-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060104-A904-DEB9-4748-2C7F4A124842"    {["Notify"          ]}
%     "Custom"                "D5060005-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060105-A904-DEB9-4748-2C7F4A124842"    {["Notify"          ]}
%     "Custom"                "D5060005-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060205-A904-DEB9-4748-2C7F4A124842"    {["Notify"          ]}
%     "Custom"                "D5060005-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060305-A904-DEB9-4748-2C7F4A124842"    {["Notify"          ]}
%     "Custom"                "D5060005-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060405-A904-DEB9-4748-2C7F4A124842"    {["Notify"          ]}
%     "Custom"                "D5060006-A904-DEB9-4748-2C7F4A124842"    "Custom"                                        "D5060602-A904-DEB9-4748-2C7F4A124842"    {["Indicate"        ]}
% 
%%
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


%% MyoInfoCharacteristic (0x0101)
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


%% FirmwareVersionCharacteristic (0x0201)
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


%% CommandCharacteristic (0x0401) myohw_command_t
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

% vibrate
% fprintf('Vibrating:\n')
% myohw_vibration_none   = 00; % < Do not vibrate.
% myohw_vibration_short  = 01; % < Vibrate for a short amount of time.
% myohw_vibration_medium = 02; % < Vibrate for a medium amount of time.
% myohw_vibration_long   = 03; % < Vibrate for a long amount of time.
% fprintf('Short\n')
% write(CommandCharacteristic,[myohw_command_vibrate 1 myohw_vibration_short])
% pause(0.5)
% fprintf('Medium\n')
% write(CommandCharacteristic,[myohw_command_vibrate 1 myohw_vibration_medium])
% pause(1)
% fprintf('Long\n')
% write(CommandCharacteristic,[myohw_command_vibrate 1 myohw_vibration_long])
% pause(1.5)

fprintf('Sleep Mode: Never\n')
myohw_sleep_mode_normal      = 0; % < Normal sleep mode; Myo will sleep after a period of inactivity.
myohw_sleep_mode_never_sleep = 1; % < Never go to sleep.
write(CommandCharacteristic,[myohw_command_set_sleep_mode 1 myohw_sleep_mode_never_sleep])

%fprintf('Deep Sleep\n')
%write(CommandCharacteristic,[myohw_command_deep_sleep 0])


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

%%
fprintf('---------------------------------\n')
fprintf('Read EMG EmgDataService (0x0005):\n')
fprintf('---------------------------------\n')

EmgData0Characteristic = characteristic(myo, 'D5060005-A904-DEB9-4748-2C7F4A124842', 'D5060105-A904-DEB9-4748-2C7F4A124842');
EmgData1Characteristic = characteristic(myo, 'D5060005-A904-DEB9-4748-2C7F4A124842', 'D5060205-A904-DEB9-4748-2C7F4A124842');
EmgData2Characteristic = characteristic(myo, 'D5060005-A904-DEB9-4748-2C7F4A124842', 'D5060305-A904-DEB9-4748-2C7F4A124842');
EmgData3Characteristic = characteristic(myo, 'D5060005-A904-DEB9-4748-2C7F4A124842', 'D5060405-A904-DEB9-4748-2C7F4A124842');

% (Optional) Doesn't appear to be needed for read
% subscribe(EmgData0Characteristic,'notification')
% subscribe(EmgData1Characteristic,'notification')
% subscribe(EmgData2Characteristic,'notification')
% subscribe(EmgData3Characteristic,'notification')
% 
fprintf('EMG Data:\n')
data1 = read(EmgData0Characteristic);
data2 = read(EmgData1Characteristic);
data3 = read(EmgData2Characteristic);
data4 = read(EmgData3Characteristic);
fprintf(['EmgData0: [' repmat('%02x ',1, 16) ']\n'], data1)
fprintf(['EmgData1: [' repmat('%02x ',1, 16) ']\n'], data2)
fprintf(['EmgData2: [' repmat('%02x ',1, 16) ']\n'], data3)
fprintf(['EmgData3: [' repmat('%02x ',1, 16) ']\n'], data4)


%% (Needs MiniVIE)
hPlot = LivePlot(8, 1000);
StartStopForm([])
while StartStopForm
    % read each characteristic and convert to int8 (+/- 127)
    data = double(typecast(uint8(read(EmgData0Characteristic,'oldest')),'int8'));
    hPlot.putdata(data(1:8) + (0:150:150*7));
    hPlot.putdata(data(9:16) + (0:150:150*7));
    data = double(typecast(uint8(read(EmgData1Characteristic,'oldest')),'int8'));
    hPlot.putdata(data(1:8) + (0:150:150*7));
    hPlot.putdata(data(9:16) + (0:150:150*7));
    data = double(typecast(uint8(read(EmgData2Characteristic,'oldest')),'int8'));
    hPlot.putdata(data(1:8) + (0:150:150*7));
    hPlot.putdata(data(9:16) + (0:150:150*7));
    data = double(typecast(uint8(read(EmgData3Characteristic,'oldest')),'int8'));
    hPlot.putdata(data(1:8) + (0:150:150*7));
    hPlot.putdata(data(9:16) + (0:150:150*7));
end

if 0 % (disabled)since this takes over console, but can be manually invokes as cell
    %% Setup notification callback
    % EmgData0Characteristic.DataAvailableFcn = @(x) fprintf('%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d\n',x);
    % EmgData0Characteristic.DataAvailableFcn = @(src,evt) disp(src);
    % src = 
    %   Characteristic with properties:
    % 
    %              Name: "Custom"
    %              UUID: "D5060105-A904-DEB9-4748-2C7F4A124842"
    %        Attributes: "Notify"
    %       Descriptors: [1x3 table]
    %  DataAvailableFcn: @(src,evt)disp(src)
    %  
    EmgData0Characteristic.DataAvailableFcn = @(src,evt) fprintf('EMG0: %4d %4d %4d %4d %4d %4d %4d %4d\n      %4d %4d %4d %4d %4d %4d %4d %4d\n', typecast(uint8(read(src,'oldest')),'int8'));
    EmgData1Characteristic.DataAvailableFcn = @(src,evt) fprintf('EMG1: %4d %4d %4d %4d %4d %4d %4d %4d\n      %4d %4d %4d %4d %4d %4d %4d %4d\n', typecast(uint8(read(src,'oldest')),'int8'));
    EmgData2Characteristic.DataAvailableFcn = @(src,evt) fprintf('EMG2: %4d %4d %4d %4d %4d %4d %4d %4d\n      %4d %4d %4d %4d %4d %4d %4d %4d\n', typecast(uint8(read(src,'oldest')),'int8'));
    EmgData3Characteristic.DataAvailableFcn = @(src,evt) fprintf('EMG3: %4d %4d %4d %4d %4d %4d %4d %4d\n      %4d %4d %4d %4d %4d %4d %4d %4d\n', typecast(uint8(read(src,'oldest')),'int8'));
    
    %% pause(5)
    
    EmgData0Characteristic.DataAvailableFcn = [];
    EmgData1Characteristic.DataAvailableFcn = [];
    EmgData2Characteristic.DataAvailableFcn = [];
    EmgData3Characteristic.DataAvailableFcn = [];
end

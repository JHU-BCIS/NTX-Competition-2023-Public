%% Create a UDP interface object to send commands to the vMPL
UdpLocalPort = 56789;
UdpDestinationPort1 = 25000; % 25100 = Left limb; 25000 = Right limb;
UdpDestinationPort2 = 25100; % 25100 = Left limb; 25000 = Right limb;
UdpAddress = '127.0.0.1'; % IP address for sending commands to own computer
hArm1 = PnetClass(UdpLocalPort,UdpDestinationPort1,UdpAddress);
hArm2 = PnetClass(UdpLocalPort,UdpDestinationPort2,UdpAddress);
hArm1.initialize(); % hArm1 is the "Handle" for sending commands to the vMPL left limb
hArm2.initialize(); % hArm2 is the "Handle" for sending commands to the vMPL left limb

upperArm1Angles = zeros(1,7); % Create array of numbers for each arm joint in limb
upperArm2Angles = zeros(1,7); % Create array of numbers for each arm joint in limb
hand1Angles = zeros(1,20); % Create array of numbers for each hand joint in limb
hand2Angles = zeros(1,20); % Create array of numbers for each hand joint in limb
upperArm1Angles(1) = 30 * pi / 180;      % Left Shoulder Flexion (+) / Shoulder Extension (-) -40/175
upperArm1Angles(2) = 0 * pi / 180;      % Left Shoulder Adduction (+) / Shoulder Abduction (-) -160/0
upperArm1Angles(3) = 0 * pi / 180;      % Left Humeral Internal Rotation (+) / Humeral External Rotation (-) -45/90
upperArm1Angles(4) = 90 * pi / 180;      % Left Elbow Flexion (+) / Elbow Extension (-) 0/150
upperArm1Angles(5) = 90 * pi / 180;      % Left Wrist Pronation (+) / Wrist Supination (-) -90/90
upperArm1Angles(6) = 0 * pi / 180;      % Left Ulnar Deviation (+) / Radial Deviation (-) -15/45
upperArm1Angles(7) = 0 * pi / 180;      % Left Wrist Flexion (+) / Wrist Extension (-) -60/60

hand1Angles(1) = 0 * pi / 180;          % Left Hand INDEX_AB_AD -20/0
hand1Angles(2) = 0 * pi / 180;          % Left Hand INDEX_MCP -30/110
hand1Angles(3) = 0 * pi / 180;          % Left Hand INDEX_PIP 0/100
hand1Angles(4) = 0 * pi / 180;          % Left Hand INDEX_DIP 0/80
hand1Angles(5) = 0 * pi / 180;          % Left Hand MIDDLE_AB_AD -20/0
hand1Angles(6) = 90 * pi / 180;          % Left Hand MIDDLE_MCP -30/110
hand1Angles(7) = 90 * pi / 180;          % Left Hand MIDDLE_PIP 0/100
hand1Angles(8) = 0 * pi / 180;          % Left Hand MIDDLE_DIP 0/80
hand1Angles(9) = 0 * pi / 180;          % Left Hand RING_AB_AD -20/0
hand1Angles(10) = 90 * pi / 180;         % Left Hand RING_MCP -30/110
hand1Angles(11) = 90 * pi / 180;         % Left Hand RING_PIP 0/100
hand1Angles(12) = 0 * pi / 180;         % Left Hand RING_DIP 0/80
hand1Angles(13) = 0 * pi / 180;         % Left Hand LITTLE_AB_AD -20/0
hand1Angles(14) = 0 * pi / 180;         % Left Hand LITTLE_MCP -30/110
hand1Angles(15) = 0 * pi / 180;         % Left Hand LITTLE_PIP 0/100
hand1Angles(16) = 0 * pi / 180;         % Left Hand LITTLE_DIP 0/80
hand1Angles(17) = 0 * pi / 180;         % Left Hand THUMB_CMC_AD_AB 0/105
hand1Angles(18) = 0 * pi / 180;         % Left Hand THUMB_CMC 0/55
hand1Angles(19) = 0 * pi / 180;         % Left Hand THUMB_MCP 0/60
hand1Angles(20) = 0 * pi / 180;         % Left Hand THUMB_DIP 0/60

upperArm2Angles(1) = 90 * pi / 180;      % Right Shoulder Flexion (+) / Shoulder Extension (-) -40/175
upperArm2Angles(2) = 0 * pi / 180;      % Right Shoulder Adduction (+) / Shoulder Abduction (-) -160/0
upperArm2Angles(3) = 0 * pi / 180;      % Right Humeral Internal Rotation (+) / Humeral External Rotation (-) -45/90
upperArm2Angles(4) = 0 * pi / 180;      % Right Elbow Flexion (+) / Elbow Extension (-) 0/150
upperArm2Angles(5) = 0 * pi / 180;      % Right Wrist Pronation (+) / Wrist Supination (-) -90/90
upperArm2Angles(6) = 0 * pi / 180;      % Right Ulnar Deviation (+) / Radial Deviation (-) -15/45
upperArm2Angles(7) = 0 * pi / 180;      % Right Wrist Flexion (+) / Wrist Extension (-) -60/60

hand2Angles(1) = 0 * pi / 180;          % Left Hand INDEX_AB_AD -20/0
hand2Angles(2) = 0 * pi / 180;          % Left Hand INDEX_MCP -30/110
hand2Angles(3) = 0 * pi / 180;          % Left Hand INDEX_PIP 0/100
hand2Angles(4) = 0 * pi / 180;          % Left Hand INDEX_DIP 0/80
hand2Angles(5) = 0 * pi / 180;          % Left Hand MIDDLE_AB_AD -20/0
hand2Angles(6) = 90 * pi / 180;          % Left Hand MIDDLE_MCP -30/110
hand2Angles(7) = 90 * pi / 180;          % Left Hand MIDDLE_PIP 0/100
hand2Angles(8) = 0 * pi / 180;          % Left Hand MIDDLE_DIP 0/80
hand2Angles(9) = 0 * pi / 180;          % Left Hand RING_AB_AD -20/0
hand2Angles(10) = 90 * pi / 180;         % Left Hand RING_MCP -30/110
hand2Angles(11) = 90 * pi / 180;         % Left Hand RING_PIP 0/100
hand2Angles(12) = 0 * pi / 180;         % Left Hand RING_DIP 0/80
hand2Angles(13) = 0 * pi / 180;         % Left Hand LITTLE_AB_AD -20/0
hand2Angles(14) = 0 * pi / 180;         % Left Hand LITTLE_MCP -30/110
hand2Angles(15) = 0 * pi / 180;         % Left Hand LITTLE_PIP 0/100
hand2Angles(16) = 0 * pi / 180;         % Left Hand LITTLE_DIP 0/80
hand2Angles(17) = 0 * pi / 180;         % Left Hand THUMB_CMC_AD_AB 0/105
hand2Angles(18) = 0 * pi / 180;         % Left Hand THUMB_CMC 0/55
hand2Angles(19) = 0 * pi / 180;         % Left Hand THUMB_MCP 0/60
hand2Angles(20) = 0 * pi / 180;         % Left Hand THUMB_DIP 0/60

msg1 = typecast(single([upperArm1Angles,hand1Angles]),'uint8'); % Generate Command msg for left arm
msg2 = typecast(single([upperArm2Angles,hand2Angles]),'uint8'); % Generate Command msg for right arm
hArm1.putData(msg1); % Send constructed command message to the vMPL using the Handle
hArm2.putData(msg2); % Send constructed command message to the vMPL using the Handle
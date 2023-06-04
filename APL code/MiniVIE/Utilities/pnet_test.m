% Test UDP communications via pnet.
% Expected output:
% ---------------------------
%
% Loaded pnet Version  2.0.5  2003-09-16 Copyright (C) Peter Rydesäter, Sweden, et al. , 1998 - 2003
% 
% Loaded pnet Version  2.0.5  2003-09-16 Copyright (C) Peter Rydesäter, Sweden, et al. , 1998 - 2003
% [PnetClass] Opened pnet socket #0 at local port: 12001; Default destination: port 45001 @ 127.0.0.1
% [PnetClass] Opened pnet socket #1 at local port: 13001; Default destination: port 45001 @ 127.0.0.1
% 
% ans =
% 
%     'Test'
% 
% [PnetClass.m] Closed pnet socket #0 at local port: 12001
% [PnetClass.m] Closed pnet socket #1 at local port: 13001



%% cleanup everything
pnet('closeall')
clear all

%% open sender
a = PnetClass(12001);
a.initialize();

%% open receiver
b = PnetClass(13001);
b.initialize();

%% send packet
a.putData('Test','127.0.0.1',13001)

%% rcv packet
char(b.getData)

%% close
a.close()
b.close()
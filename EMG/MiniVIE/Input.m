%% Create an object for UDP interface to the Myo Armband
hMyo = Inputs.MyoUdp.getInstance();
hMyo.initialize();

%% Get data and plot. emgData size is [1000 samples x 8 channels]
emgData = hMyo.getData;
plot(emgData)
xlabel('Sample Number'); ylabel('EMG Signal')

hViewer = GUIs.guiSignalViewer(hMyo); % View Myoband voltage signals in real time

classdef IntanUdp < Inputs.SignalInput
    % Class for interfacing Intan Demo Code via pnet.
    %     
    %     % Test usage:
    %     obj = Inputs.IntanUdp.getInstance;
    %     obj.initialize();
    %     hViewer = GUIs.guiSignalViewer(a);
    properties
        UdpStreamReceivePortNumLocal = 14001;
        EMG_GAIN = 1.0e4;
    end
    properties (SetAccess = private)
        UdpTotalReceivedSamples = 0;
        UdpTotalReceiveTime = datetime('now');
        UdpLastTime = datetime('now');
        UdpLastSampleCount = 0;

        IsInitialized = 0;
        hUdpSocket = [];
        dataBuffer;
    end
    methods (Access = private)
        function obj = IntanUdp
            % Creator is private to force singleton
        end
    end
    methods
        %initialize(obj);
        function [ status ] = initialize(obj)
            % Initialize network interface to NFU.
            % [ status ] = initialize(obj)
            %
            % status = 0: no error
            % status < 0: Failed
            obj.SampleFrequency = 1000; % Hz
            obj.ChannelIds = 1:16;
            
            status = 0;
            
            if obj.IsInitialized
                fprintf('[%s] UDP Comms already initialized\n',mfilename);
                return
            end
            
            % Open a udp port to receive streaming data on
            obj.hUdpSocket = PnetClass(obj.UdpStreamReceivePortNumLocal);
            if ~obj.hUdpSocket.initialize()
                fprintf(2,'[%s] Failed to initialize udp socket\n',mfilename);
                status = -1;
                return
            elseif (obj.hUdpSocket.hSocket ~= 0)
                fprintf(2,'[%s] Expected receive socket id == 0, got socket id == %d\n',mfilename,obj.hUdpSocket.hSocket);
            end

            obj.dataBuffer = zeros(obj.NumChannels,5000);
            
            obj.IsInitialized = true;
            
        end
        function data = getData(obj,numSamples,idxChannel)
            %data = getData(obj,numSamples,idxChannel)
            % get data from buffer.  most recent sample will be at (end)
            % position.
            % dataBuffer = [NumSamples by NumChannels];
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
            
            cellData = obj.hUdpSocket.getAllData(); % read available packets

            % Loop through all available packets and find cpch data
            for i = 1:length(cellData)
                numChannelsInPacket = 16;
                numNewSamplesInPacket = 10;
                thisDataArray = typecast(cellData{i},'single');
                if numel(thisDataArray) == (numNewSamplesInPacket * numChannelsInPacket)
                    thisData = reshape(thisDataArray,[numNewSamplesInPacket, numChannelsInPacket]);
                    % Place new data in the buffer.  Note this won't overrun
                    % the buffer since there are only 10 samples per packet
                    obj.dataBuffer = circshift(obj.dataBuffer,[0 -numNewSamplesInPacket]);
                    obj.dataBuffer(1:numChannelsInPacket,end-numNewSamplesInPacket+1:end) = thisData';

                    % Add a counter for new samples
                    obj.UdpTotalReceivedSamples = obj.UdpTotalReceivedSamples + numNewSamplesInPacket;
                else
                    warning('[%s] Expected %d values = %d channels x %d newSamples.  Got %d values\n',mfilename, ...
                        numNewSamplesInPacket*numChannelsInPacket, numChannelsInPacket, numNewSamplesInPacket, numel(thisDataArray));
                end                
            end

            % Calculate rate information
            elapsedTime = seconds(datetime('now') - obj.UdpLastTime);
            if elapsedTime > 2.0 % seconds
                rate = (obj.UdpTotalReceivedSamples - obj.UdpLastSampleCount) ./ elapsedTime;
                fprintf('[%s] Current Data Rate is: %8.1f Hz\n', mfilename, rate)
                obj.UdpLastSampleCount = obj.UdpTotalReceivedSamples;
                obj.UdpLastTime = datetime('now');
            end

            % return as many samples as requested
            dataBuff = obj.dataBuffer(:,end-numSamples+1:end)';
            
            data = obj.EMG_GAIN .* double(dataBuff(:,idxChannel));
        end
    end
    methods (Static)
        function [obj, hViewer] = Default
            % [obj, hViewer] = Inputs.IntanUdp.Default();
            % Test usage:
            obj = Inputs.IntanUdp.getInstance;
            obj.initialize();
            hViewer = GUIs.guiSignalViewer(obj);
        end
        function singleObj = getInstance(cmd)
            persistent localObj
            if nargin < 1
                cmd = 0;
            end
            
            if cmd < 0
                fprintf('[%s] Deleting Udp comms object\n',mfilename);
                try %#ok<TRYNC> 
                    obj.hUdpSocket.close();
                end
                localObj = [];
                return
            end
            
            if isempty(localObj) || ~isvalid(localObj)
                fprintf('[%s] Calling constructor\n',mfilename);
                localObj = Inputs.IntanUdp;
            else
                fprintf('[%s] Returning existing object\n',mfilename);
            end
            singleObj = localObj;
        end
        function isReady = isReady(~) % Consider removing extra arg
            isReady = 1;
        end
        function start(~)
        end
        function stop(~)
        end
        function close(~)
        end
    end
end

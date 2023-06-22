classdef LivePlot < handle
    % General purpose function for making a strip chart plot
    % Usage: h = LivePlot(3,100,{'X' 'Y' 'Z'})
    %  putdata(h,rand(3,1))
    %  ...
    %
    % Created 2009-Apr-21 Robert Armiger, Johns Hopkins University Applied
    % Physics Lab
    
    %
    % $Log: LivePlot.m  $
    % Revision 1.11 2010/06/16 22:27:31EDT armigrs1-a 
    % added Log and better warning message on bad data sizes
    % 
    
    properties
        hFig
        hAxes
        hLines
        hText

        AxisLimits = []

        id = tempname;
    end
    methods
        function obj = LivePlot(nLines,MAX_SAMPLES,cellLegendLabels,figNum)

            if nargin < 1
                nLines = 1;
            end
            if nargin < 2
                MAX_SAMPLES = 5000;
            end
            if nargin < 3
                lineNum = 1:nLines;
                lineTxt = num2str(lineNum(:));
            else
                lineTxt = cellLegendLabels;
            end

            if nargin < 4
                figNum = 1;
            end
            
            obj.hFig = figure(figNum);
            clf(obj.hFig,'reset');

            obj.hAxes  = gca;
            obj.hLines = plot(zeros(MAX_SAMPLES,nLines));

            %h = legend(obj.hLines,lineTxt,'Location','eastoutside');
            %set(h,'Interpreter','None');

            obj.hText = zeros(size(obj.hLines));
            for i = 1:nLines
                obj.hText(i) = text(1.02*MAX_SAMPLES,0,lineTxt(i),'Interpreter','None');
                set(obj.hText(i),'Color',get(obj.hLines(i),'Color'));
            end

        end
        function putdata(obj,newData,isReset)

            persistent tLast yLimits

            if nargin == 3 && isReset
                tLast = [];
                yLimits = [];
                return
            end

            if isempty(tLast)
                tLast = clock;
                yLimits = [-eps eps];
            end

            nLines = length(obj.hLines);
            if length(newData) ~= nLines
                fprintf('LivePlot:Bad input data. Expected %d point(s), got %d\n',nLines,length(newData));
                return
            end

            dataRange = zeros(nLines,2);

            for iLine = 1:nLines
                data = get(obj.hLines(iLine),{'XData','YData','ZData'});

                yData = data{2};

                %%Shift the y-data and add the new samples
                yData = [yData(2:end) newData(iLine)];

                dataRange(iLine,:) = [min(yData(:)) max(yData(:))];

                set(obj.hLines(iLine),'YData',yData);

                pos = get(obj.hText(iLine),'Position');
                set(obj.hText(iLine),'Position',[pos(1) mean(yData(end-5:end)) pos(3)])

            end

            if etime(clock,tLast) > 0.1
%                 drawnow
%                 axLim(1) = min(min(dataRange(:)),yLimits(1));
%                 axLim(2) = max(max(dataRange(:)),yLimits(2));
                axLim(1) = min(dataRange(:));
                axLim(2) = max(dataRange(:));
                yLimits = axLim;
                if isempty(obj.AxisLimits)
                    if all(yLimits == 0)
                        yLimits = [-1 1];
                    else
                        ylim(obj.hAxes,yLimits.*1.02);
                    end
                else
                    ylim(obj.hAxes,obj.AxisLimits);
                end
                %ylim(obj.hAxes,[-5 5]);
                tLast = clock;
            end
        end
        function close(obj)
            if ishandle(obj.hFig)
                delete(obj.hFig);
            end
        end
    end
end

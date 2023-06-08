% a = 1;
% format shortg
% c = clock
% c = c(4)* 60 * 60 + c(5)* 60 + c(6)
% 
% h = [2 3 4 5 6 64 4 5]
% 
% c = [8.99]
% 
% timestamp = [c h]
% 
% timestamp2 = timestamp + 1
% 
% all = timestamp
% all = [timestamp; timestamp2]
% all = [all; timestamp]
% 
% emg = all 
% 
% cursor = [1 1]
% 
% tb = table(cursor,emg) ;
% Mdl = fitrnet(X,Y) 
% Mdl = fitrsvm(tb,'y','KernelFunction','gaussian');
% YFit = predict(Mdl,tb);
% 
% function loopWithWindow()
%     Create the main window
%     fig = uifigure('Name', 'Series Data Collection', 'Position', [100 100 300 150]);
%     
%     Calculate button position
%     btnWidth = 100;
%     btnHeight = 22;
%     btnX = (fig.Position(3) - btnWidth) / 2;
%     btnY = (fig.Position(4) - btnHeight) / 2;
%     
%     Create the button
%     btn = uibutton(fig, 'Text', 'Stop', 'Position', [btnX btnY btnWidth btnHeight]);
% 
%     Initialize loop condition
%     stopLoop = false;
%     
%     Button callback function
%     btn.ButtonPushedFcn = @(~,~) stopLoopCallback();
% 
%     Loop while the stopLoop condition is false
%     while ~stopLoop
%         Perform your computations or tasks within the loop here
%         ...
%         
%         Update the GUI and process callbacks
%         drawnow;
%     end
%     
%     Clean up
%     delete(fig);
%     
%     Nested function to handle button callback
%     function stopLoopCallback()
%         stopLoop = true; % Set the stopLoop condition to true
%     end
% end

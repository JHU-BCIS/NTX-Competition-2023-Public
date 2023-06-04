% Objective of this function is to connect myo, classify basic gestures,
% and use a combination of EMG and gyro to control cursor for painting app

% Get Input Source
SignalSource = Inputs.MyoUdp.getInstance();
SignalSource.initialize();
%SignalSource.preview()
SignalSource.NumSamples = 150;

% Setup trainig data container
TrainingData = PatternRecognition.TrainingData();

% Setup classifier
SignalClassifier = SignalAnalysis.Lda();
SignalClassifier.initialize(TrainingData);
SignalClassifier.setClassNames({'No Movement' 'Wrist Flex' 'Wrist Extend' 'Spherical Grasp'});
SignalClassifier.setActiveChannels(1:8);
SignalClassifier.NumMajorityVotes = 35;

% Train
TrainingInterface = PatternRecognition.SimpleTrainer();

%% One time training:
if 0
    %%
    TrainingInterface.NumRepetitions = 2;  % <-- Adjust (2 to 3 typical)
    TrainingInterface.ContractionLengthSeconds = 2; % <-- Time to hold contraction (avoid muscle fatigue)
    TrainingInterface.DelayLengthSeconds = 3; % <-- Recovery Time in seconds between contractions
    TrainingInterface.initialize(SignalSource,SignalClassifier,TrainingData);
    TrainingInterface.collectdata();
end
%TrainingData.loadTrainingData('*.trainingData');
TrainingData.loadTrainingData('myo_gesture.trainingData');

SignalClassifier.train();
SignalClassifier.computeError();

%% Test the classification:
x = 0;
y = 0;
screen =  get(0,'ScreenSize');
last_class = '';
import java.awt.Robot;
import java.awt.event.*;

while true
    drawnow
    SignalSource.update()
    
    % classify
    windowData = SignalSource.getFilteredData();
    features2D = SignalClassifier.extractfeatures(windowData);
    activeChannelFeatures = features2D(SignalClassifier.getActiveChannels,:);
    [~,class_id] = SignalClassifier.classify(reshape(activeChannelFeatures',[],1));    
    classNames = SignalClassifier.getClassNames;
    this_class = classNames{class_id};
    disp(this_class)

    % get motion
    gyro = SignalSource.Gyroscope';
    gyro(abs(gyro) < 2) = 0;
    R_Myo = SignalSource.getRotationMatrix;    
    ang_velocity_global = R_Myo * gyro;
    
    x = x + 2 * -ang_velocity_global(3);
    y = y + 2 * -ang_velocity_global(1);
    
    x = min(screen(3),max(0, x));
    y = min(screen(4),max(0, y));
        
    % Import Java classes for mouse control and button click events
    robot = Robot; 
    robot.mouseMove(x, y);

    % CHange Color
    if strcmpi(last_class,'Spherical Grasp') && strcmpi(this_class,'No Movement') 
        robot.mousePress(InputEvent.BUTTON1_MASK);
        robot.mouseRelease(InputEvent.BUTTON1_MASK);
    end
    
    % Clear Canvas
    if strcmpi(last_class,'Wrist Flex') && strcmpi(this_class,'No Movement')
        robot.keyPress(java.awt.event.KeyEvent.VK_SPACE);
        robot.keyRelease(java.awt.event.KeyEvent.VK_SPACE);
    end
    
    % Done
    if strcmpi(last_class,'Wrist Extend') && strcmpi(this_class,'No Movement') 
        break
    end
    
    
    % store the last  class
    last_class = classNames{class_id};
end
disp('Done')

%%
return
%%
f = Presentation.Pollock.launch_flash();
system([f ' &'])

%% Start myo_server (python)
cwd = pwd
cd('C:\git\minivieextended\python\minivie\inputs')
system(strcat('py -3 myo_server.py -x single_myo.xml &'));
cd(cwd)
%%




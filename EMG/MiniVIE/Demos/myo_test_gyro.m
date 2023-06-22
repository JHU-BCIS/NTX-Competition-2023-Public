% Demo myo control using the gyro for drawing
% Optionally start the myo streamer.  
% Animate a graphical myo
% show a 2d drawing pen, controlled by the gyros


a = Inputs.MyoUdp.getInstance;
a.initialize();

if 0
    %% Start MyoUdp
    f = fullfile(fileparts(which('MiniVIE')),'+Inputs','MyoUdp.exe');
    system(strcat(f,' &'));
    
    %% Start myo_server (python)
    cwd = pwd
    cd('C:\git\minivieextended\python\minivie\inputs')
    system(strcat('py -3 myo_server.py -x single_myo.xml &'));
    cd(cwd)
    
    %%
    a.preview
    %%
    StartStopForm([])
    while StartStopForm()
        a.update()
        %a.getEulerAngles
        %a.Accelerometer
        %a.Orientation
        %a.getRotationMatrix
        a.Gyroscope
    end
end

%%
clf

hAxes = subplot(2,1,1);
title(hAxes,'Myo 3D')

% setup frames
hGlobal = PlotUtils.triad(eye(4),20);
hTriad = PlotUtils.triad(eye(4),50);

axis_range = 60;
axis([-axis_range axis_range -axis_range axis_range -axis_range axis_range])
daspect([1 1 1])


% create a box for the myo band pods
v = [
    0 0 0
    1 0 0
    1 1 0
    0 1 0
    0 0 1
    1 0 1
    1 1 1
    0 1 1];
% center at 0, unit length
v(:,1) = (v(:,1) - 0.5);
v(:,2) = (v(:,2) - 0.5);
v(:,3) = (v(:,3) - 0.5);
% connect the vertices
f = [1 2 3 4
    1 2 6 5
    2 3 7 6
    3 4 8 7
    4 1 5 8
    5 6 7 8
    ];
% scale to mm
v(:,3) = v(:,3) * 8.4;
v(:,2) = v(:,2) * 21;
v(:,1) = v(:,1) * 48;
% replicate pods radially
hMyo = hgtransform('Parent',hAxes);
for i = 1:8
    hOffset(i) = hgtransform('Parent',hMyo,'Matrix',makehgtform('xrotate',pi/4 * (i+4),'translate',[0.0 0.0 34]));
    hPodPatch(i) = patch('Faces', f, 'Vertices', v, 'FaceAlpha', 0.3, 'Parent', hOffset(i));
end
daspect([1 1 1])
% hPodPatch(1).FaceColor = 'r'
% hPodPatch(2).FaceColor = 'y'
view(-30,30)

% Add logo
hLogoT = hgtransform('Parent',hOffset(4));  % Logo is on Pod #4

img = imread('thalmic_labs.png');     % Load a sample image
img = double(img)./255;
img(img == 1) = NaN;
% img(img == 255) = 0;
xImage = [-1 1; -1 1];   % The x data for the image corners
yImage = [0 0; 0 0];             % The y data for the image corners
zImage = [1 1; -1 -1];   % The z data for the image corners
hLogoSurf = surf(xImage,yImage,zImage,...    % Plot the surface
    'CData',img,...
    'FaceColor','texturemap','Parent',hLogoT);
set(hLogoSurf,'FaceAlpha',0.3, 'EdgeColor','None');
logo_z = 4.3; % value slightly larger than pod height
hLogoT.Matrix = makehgtform('yrotate',pi/2, 'zrotate',pi/2, 'translate', [0 logo_z 0], 'scale',6);

hStatusLine = line([-20 -20],[-5 5],[logo_z logo_z],'Parent',hOffset(4),'LineWidth',4,'Color',squeeze(img(185,150,:)));

set([hPodPatch hLogoSurf],'FaceAlpha',0.8)

%% Create Mouse axes
%
hMouseAxes = subplot(2,1,2);

title(hMouseAxes,'Mouse control')

hTrail = plot3(0,0,0,'r.-','LineWidth',3);
axis([-1000 1000 -1000 1000 -1000 1000]);
daspect([1 1 1])
view(2)
z = 0;
y = 0;
x = 0;

trail_length = 450;
x_ = nan(1,trail_length);
y_ = nan(1,trail_length);
z_ = nan(1,trail_length);

% Animate updates
cmap = colormap('hot');
set(hPodPatch,'FaceColor','Black')

StartStopForm([])
while StartStopForm
    drawnow
    a.update()
    
    mavEmg = mean(abs(a.getData(150,1:8)));
    for i = 1:8
        cmap_idx_val = max(1,min(64,round(mavEmg(i)*64)));
        set(hPodPatch(i),'FaceColor',cmap(cmap_idx_val,:) )
    end
    
    R_Myo = a.getRotationMatrix;
    T_Myo = [R_Myo [0 0 0]'; 0 0 0 1];
    set(hTriad, 'Matrix', T_Myo);
    set(hMyo, 'Matrix', T_Myo);
    
    ang_velocity_myo = a.Gyroscope';
    ang_velocity_global = a.getRotationMatrix * a.Gyroscope';
    %
    
    x = x + 2 * -ang_velocity_global(3);
    y = y + 2 * -ang_velocity_global(2);
    
    x = min(1000,max(-1000, x));
    y = min(1000,max(-1000, y));
    
    x_ = [x x_(1:end-1)];
    y_ = [y y_(1:end-1)];
    z_ = [z z_(1:end-1)];
    
    % update trail
    set(hTrail,'XData',x_);
    set(hTrail,'YData',y_);
    set(hTrail,'ZData',z_);
    
end

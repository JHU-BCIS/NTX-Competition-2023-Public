% Demo an animated myo armband 
%   This will show the armband on the MiniV arm, and color each pod in demo
%   mode.  This could be used to animate myo activity for actual usage
% Revisions:
% 5/8/2020 Armiger: Created 


% Create a handle to the MiniV animated arm
hFig = UiTools.create_figure('test');
hFig.ToolBar = 'figure';
set(hFig,'WindowStyle','docked')
p = get(hFig,'Position');
p = [300 150 800 600];
set(hFig,'Position',p)
hAxes = axes('Parent',hFig);
hold(hAxes,'on');
hUser = Presentation.MiniV(hAxes,1,[1 1 1],1);
view(hAxes,0,0);
axis(hAxes,'equal')
hLight = light('Parent',hAxes);
camlight(hLight,'left');
axis(hAxes,[0.1 0.25 -0.1 0.1 0.35 0.55])
set([hUser.handle.hPatch],'Clipping','on')
hAxes.XTick = []
hAxes.YTick = []
hAxes.ZTick = []

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
v(:,1) = v(:,1) * 8.4;
v(:,2) = v(:,2) * 21;
v(:,3) = v(:,3) * 48;
% replicate pods radially
hMyo = hgtransform('Parent',hAxes);
for i = 1:8
    hOffset(i) = hgtransform('Parent',hMyo,'Matrix',makehgtform('zrotate',pi/4 * i,'translate',[34 0.0 0.0]))
    hPodPatch(i) = patch('Faces', f, 'Vertices', v, 'FaceAlpha', 0.3, 'Parent', hOffset(i))
end

%% Add logo

hLogo = hgtransform('Parent',hMyo)

% img = imread('myo_logo.png');     % Load a sample image
img = imread('thalmic_labs.png');     % Load a sample image
img(img == 255) = NaN;
xImage = [-0.5 0.5; -0.5 0.5];   % The x data for the image corners
yImage = [0 0; 0 0];             % The y data for the image corners
zImage = [0.5 0.5; -0.5 -0.5];   % The z data for the image corners
logo_surf = surf(xImage,yImage,zImage,...    % Plot the surface
    'CData',img,...
    'FaceColor','texturemap','Parent',hLogo);
set(logo_surf,'FaceAlpha',0.8, 'EdgeColor','None');
hLogo.Parent = hOffset(6)
hLogo.Matrix = makehgtform('zrotate',pi/2, 'translate', [0 -5 0], 'scale',12)


%% Align with arm
hMyo.Matrix = makehgtform(...
    'translate',[0.141 0.023 0.5],... GCS translation
    'xrotate',-0.45,...
    'yrotate',-0.6,...
    'zrotate',0,... %spin
    'translate',[0.001 0 -0.02],... LCS translation
    'scale',0.00062);

set(hPodPatch,'FaceAlpha',0.8)


%% Animate pod activation (demo)
video = false
if video
    v = VideoWriter('myo3.avi');
    open(v);
end

%cmap = colormap('copper');
cmap = hot; % colormap('hot');

set(hPodPatch,'FaceColor','Black')
hUser.set_upper_arm_angles_degrees([0 0 0 0 0 0 0])
hUser.redraw

for i = 1:8
    for j = 1:4:64
        set(hPodPatch(9-i),'FaceColor',cmap(65-j,:) )
        hUser.set_upper_arm_angles_degrees([0 0 0 0 (i+j/64)*10 0 0])
        hUser.redraw
        drawnow
        if video
            frame = getframe(hFig);
            writeVideo(v,frame);
        end
    end
end

if video
    close(v);
end







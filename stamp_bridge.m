% Loop through EMG data, and if the mediapipe timestamp is within .050 ms
% or some arbitrary value, then you add the mp values in the row of that
% EMG data, so one mp datapoint may be distributed to multiple, varying
% amounts of EMG data
dt = duration(0, 0, 0, 50);
dt.Format = 'mm:ss.SSS';
Elength = size(bigTable); Elength = Elength(1);
Mlength = size(bigMTable); Mlength = Mlength(1);
i = 1;
j = 1; %points to where we are in mediapipe data
foundMPV = false;
% done = false;
for i = 1:Elength
    %iterate through mediapipe values
    jcopy = j;
    while(foundMPV == false && j < Mlength)
%         disp(jcopy);
        if( (bigMTable{j, 7} - bigTable{i, 10} < dt) && (bigMTable{j, 7} - bigTable{i, 10} > -dt) )
%             disp(i);
%             disp(j);
            bigTable{i, 11} = bigMTable{j, 7};
            bigTable{i, 12} = bigMTable{j, 2};
            bigTable{i, 13} = bigMTable{j, 3};
            bigTable{i, 14} = bigMTable{j, 4};
            bigTable{i, 15} = bigMTable{j, 5};
            bigTable{i, 16} = bigMTable{j, 6};
%             disp('found an MPV');
            jcopy = j;
            foundMPV = true;
            break;
        end
        j = j + 1;
        if(j >= Mlength)
            j = jcopy;
            break;
        end
    end
    foundMPV = false;
    
end

% bigTable{i, 11} = bigMTable{j, 7};
%             bigTable{i, 12} = bigMTable{j, 2};
%             bigTable{i, 13} = bigMTable{j, 3};
%             bigTable{i, 14} = bigMTable{j, 4};
%             bigTable{i, 15} = bigMTable{j, 5};
%             bigTable{i, 16} = bigMTable{j, 6};
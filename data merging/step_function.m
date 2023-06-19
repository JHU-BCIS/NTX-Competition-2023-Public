


% iterate through mediapipe
for i = 2:(Elength - 1)
    if( bigTable{i, 11} == bigTable{i+1, 11} )
        k = i+1;
        count = 2;
        % while loop tells us how many we have in a row
        disp(k);
        while( bigTable{k, 11} == bigTable{k+1, 11} )
            count = count+1;
            k = k+1;
        end
        % i is the first identical value, k is the last
        
%             mid = (i + k)/2;
            % bigTable{i - 1, 12} && bigTable{j + 1, 12} 
            prevX = bigTable{i-1, 11};
            afterX = bigTable{k+1, 11};
            
            thumbprev = bigTable{i-1, 12};
%             disp(j);
            thumbafter = bigTable{k+1, 12};

            indexprev = bigTable{i-1, 13};
            indexafter = bigTable{k+1, 13};

            midprev = bigTable{i-1, 14};
            midafter = bigTable{k+1, 14};

            ringprev = bigTable{i-1, 15};
            ringafter = bigTable{k+1, 15};

            littleprev = bigTable{i-1, 15};
            littleafter = bigTable{k+1, 15};

            x = [prevX afterX];
            x = seconds(x);

            y = [thumbprev thumbafter];
            c = [[1; 1]  x(:)]\y(:);
            m = c(2); b = c(1);

            y1 = [indexprev indexafter];
            c = [[1; 1]  x(:)]\y1(:);
            m1 = c(2); b1 = c(1);
    
            y2 = [midprev midafter];
            c = [[1; 1]  x(:)]\y2(:);
            m2 = c(2); b2 = c(1);

            y3 = [ringprev ringafter];
            c = [[1; 1]  x(:)]\y3(:);
            m3 = c(2); b3 = c(1);

            y4 = [littleprev littleafter];
            c = [[1; 1]  x(:)]\y4(:);
            m4 = c(2); b4 = c(1);

            inc = ( x(2) - x(1) )/(count + 1);

            % Loop through from i to j
            %  newthumbvalue = m*( bigTable{i-1, 11} + inc*(j-i+1) ) + b
            for j = i:k
                bigTable{j, 12} = m*( seconds(bigTable{i-1, 11}) + inc*(j-i+1) ) + b;
                bigTable{j, 13} = m1*( seconds(bigTable{i-1, 11}) + inc*(j-i+1) ) + b1;
                bigTable{j, 14} = m2*( seconds(bigTable{i-1, 11}) + inc*(j-i+1) ) + b2;
                bigTable{j, 15} = m3*( seconds(bigTable{i-1, 11}) + inc*(j-i+1) ) + b3;
                bigTable{j, 16} = m4*( seconds(bigTable{i-1, 11}) + inc*(j-i+1) ) + b4;
            end
    end
end
      

    
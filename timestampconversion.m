bigTable = readtable('EMGdata.csv');
times = table2cell(bigTable(:, 1));
for i = 1:size(times)
    %convert time from duration to string and cut off hours
    times{i} = string(times{i}); 
    times{i} = extractAfter(times{i}, ':');
    
    %convert back to duration after the cut and then format correctly
    times{i} = duration(times{i}, 'InputFormat', 'mm:ss.SSS');
    times{i} = duration(times{i}, 'Format', 'mm:ss.SSS');
end

%%add 7th row with new timestamps
Esize = size(times);
length = Esize(1);
for i = 1:length
    bigTable{i, 10} = times{i};
end

bigTable = renamevars(bigTable, 'Var10', 'New times');

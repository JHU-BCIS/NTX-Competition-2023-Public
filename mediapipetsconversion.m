bigMTable = readtable('mediapipe.csv');
Mtimes = table2cell(bigMTable(:,1));

for i= 1:size(Mtimes)
    Mtimes{i} = string(Mtimes{i});
    Mtimes{i} = extractAfter(Mtimes{i}, ':');

    Mtimes{i} = duration(Mtimes{i}, 'InputFormat', 'mm:ss.SSS');
    Mtimes{i} = duration(Mtimes{i}, 'Format', 'mm:ss.SSS');
end
size_ = size(Mtimes);
length = size_(1);
for i = 1:length
    bigMTable{i, 7} = Mtimes{i};
end

bigMTable = renamevars(bigMTable, 'Var7', 'New times');
    
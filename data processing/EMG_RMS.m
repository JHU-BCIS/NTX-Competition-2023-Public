filename = "EMG_data_20230622_003542.csv";
EMG_table = readtable(filename);
raw_EMG = table2array(EMG_table(:,2:9)); % extracts the EMG data without time stamps
rms_EMG = sqrt(movmean(raw_EMG.^2,100,1)); % calculates the root mean square of along each column in a moving window of 50 rows

% visualizing the raw vs. rms EMG data for all 8 channels
% clf
% figure
% for i = 1:8
%     subplot (8,1,i)
%     hold on
%     plot(raw_EMG(:,i))
%     plot(rms_EMG(:,i))
%     legend("raw EMG "+i, "rms EMG "+i)
%     hold off
% end

%export the calculated root mean square of EMG signal
EMG_table(:,2:9) = array2table(rms_EMG);
writetable(EMG_table, "RMS_" + filename);
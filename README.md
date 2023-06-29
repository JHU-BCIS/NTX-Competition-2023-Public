# NTX-Competition-2023-Public
Hello! We are the Johns Hopkins Undergraduate Brain Computer Interface Society. 

In this project, we aim to establish a system for intuitive continuous neuroprosthesis control based on machine-learning regression. At the preliminary stage, we have trained a Random Forest Regression model that decodes forearm EMG signals into finger angle contractions.

To acquire EMG data from the Myo Armband, we have used [MiniVIE](https://bitbucket.org/rarmiger/minivie/src/master/), which is an open source package library based on the Johns Hopkins University Applied Physics Laboratory Virtual Integration Environment (JHU/APL VIE). Though the Myo Armband is discontinued, it is still available second-hand, and other EMG hardware are also compatible with MiniVIE.

To measure finger angles in an affordable manner, we adopted [AI Hand Pose Estimation with MediaPipe](https://github.com/nicknochnack/AdvancedHandPoseWithMediaPipe), which is a variant of the open-source [MediaPipe Hand Recognition](https://developers.google.com/mediapipe/solutions/vision/gesture_recognizer#get_started) package.

In the future, we will employ more accurate regression algorithms for decoding, and explore the possibilities of using both EMG and EEG for intuitive continuous neuroprosthesis control. Thanks to the generous support from NTX and OpenBCI, we have acquired an Ultracortex "Mark IV" EEG Headset that we may work with. We look forward to continue this project into the next year’s NTX student clubs competition. 



## Pipeline

### EMG data acquisition using Myo Armband

To link the MyoArmband to you PC/mac, install “Myo Connect” using the installers from [Downloads – Jake Chapeskie](http://www.jakechapeskie.com/wp_dir/myo/downloads/). Linux versions for Myo Connect are also available on the Internet, though we have not used any and therefore have not included one.

To start acquiring data, first run “EMG/MiniVIE/+Inputs/MyoUdp” (.exe or others based on your operating system). Then go to “EMG/MiniVIE/MiniVIE.m”, and run the code in MATLAB. On the opened GUI, go to the “Input Source” tab, and select “ThalmicLabs MyoUdp”.

To collect Myoband data and save in a csv. file, run “outputSeriesData(obj) ” in the MATLAB command line.

Please refer to “EMG/MiniVIE/Readme.txt” for more details of using MiniVIE.

### Finger angle acquisition using MediaPipe

Open the built-in webcam or connect a webcam to your computer first. Go to “mediapipe/finger_angles.py” and run the code in Python. This shall open a live view of what the webcam is capturing. If this window does not open up, try selecting a different camera by modifying finger_angles.py, instructions are commented in the code.

Press “Q” once to reload the live view. Repeat until the live view labels the your hand as “Left” or “Right”. If your hand is labeled incorrectly, clearly show both your hands in the camera, and make sure all your fingers are visible. Once your hand is recognized correctly, press “Q” to reload for one last time. The next live view should display the contraction angle of each of your fingers, which will be stored in a csv. file. Once data collection is done, press “Q” again to quit the live view.

### Extract Feature from EMG signal

After collecting EMG recordings, copy the generated csv file to the “data processing” folder

### Merging EMG data with finger angle data

Copy the EMG csv. file and the MediaPipe csv. file to the “data merging”, and follow the instructions in “data merging/README” to merge the EMG and the MediaPipe files for model training.

### Model Training

Copy the combined scv. file to the “decoding” folder. Run the “decoding/RFRegressor.ipynb” code block by block to train the Random Forest Regressor model. 

### Output Processing

This is an extra step that we’ve taken to account for the unideal performance of the regressor. At the current stage, We are observing significant high-frequency noise in the output signal, so we’ve attempted to reduce that through low-pass filtering and envelope capturing.

Copy the “y_text.csv” and the “y_pred.csv” from the “decoding” folder to the “data processing” folder. Then run the “data processing/output_filter.mlx” file block by block. This will process and visualize the ground truth (y_test), the predicted values (y_pred), and the processed predicted values.

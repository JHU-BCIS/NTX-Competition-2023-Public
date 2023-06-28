# NTX-Competition-2023-Public
Hello! We are the Johns Hopkins Undergraduate Brain Computer Interface Society. 

In this project, we aim to establish a system for intuitive continuous neuroprosthesis control based on machine-learning regression. At the preliminary stage, we have trained a Random Forest Regression model that decodes forearm EMG signals into finger angle contractions.

To acquire EMG data from the Myo Armband, we have used [MiniVIE](https://bitbucket.org/rarmiger/minivie/src/master/), which is an open source package library based on the Johns Hopkins University Applied Physics Laboratory Virtual Integration Environment (JHU/APL VIE). Though the Myo Armband is discontinued, it is still available second-hand, and other EMG hardware are also compatible with MiniVIE.

To measure finger angles in an affordable manner, we adopted [AI Hand Pose Estimation with MediaPipe](https://github.com/nicknochnack/AdvancedHandPoseWithMediaPipe), which is a variant of the open-source [MediaPipe Hand Recognition](https://developers.google.com/mediapipe/solutions/vision/gesture_recognizer#get_started) package.

In the future, we will employ more accurate regression algorithms for decoding, and explore the possibilities of using both EMG and EEG for intuitive continuous neuroprosthesis control. Thanks to the generous support from NTX and OpenBCI, we have acquired an Ultracortex "Mark IV" EEG Headset that we may work with. We look forward to continue this project into the next year’s NTX student clubs competition. 

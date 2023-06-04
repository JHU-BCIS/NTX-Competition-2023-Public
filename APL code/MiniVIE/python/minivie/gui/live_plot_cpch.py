# Simple plot function for showing the EMG stream
# Requires matplotlib
#
# To run from command line:
# > python -m gui.test_live_plot.py
#
# Test function can also be 'double-clicked' to start

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np
import pattern_rec.feature_extract
from pattern_rec import features_selected
from pattern_rec import features
# import pattern_rec

# Ensure that the minivie specific modules can be found on path allowing execution from the 'inputs' folder
import os
if os.path.split(os.getcwd())[1] == 'gui':
    import sys
    sys.path.insert(0, os.path.abspath('..'))
from inputs import cpch_serial
src = cpch_serial.CpchSerial(port="COM9", bioamp_mask=0x00FF, gpi_mask=0x0000)
src.num_samples = 3000
src.num_samples = 150
src.connect()
global last_d
last_d = None
global last_f
last_f = None


FeatureExtract = pattern_rec.feature_extract.FeatureExtract()
select_features = pattern_rec.features_selected.FeaturesSelected(FeatureExtract)
# select_features.create_instance_list()

FeatureExtract.attach_feature(pattern_rec.features.Mav())
FeatureExtract.attach_feature(features.CurveLen())
FeatureExtract.attach_feature(features.Zc(zc_thresh=0.02))
FeatureExtract.attach_feature(features.Ssc())
# FeatureExtract.attach_feature(features.Wamp())
# FeatureExtract.attach_feature(features.Var())
# FeatureExtract.attach_feature(features.Vorder())
# FeatureExtract.attach_feature(features.LogDetect())
# FeatureExtract.attach_feature(features.EmgHist())
# FeatureExtract.attach_feature(features.AR())
# FeatureExtract.attach_feature(features.Ceps())


style.use('dark_background')
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
fig.canvas.manager.set_window_title('EMG Preview')


def animate(_):
    global last_d
    global last_f

    d = src.get_data() * 1  # *1 for a shallow copy
    if (d == last_d).all():
        print('Got same result')
    else:
        last_d = d

    f2, f, imu, rot_mat = FeatureExtract.get_features(d)
    if (f == last_f).all():
        print('Got same f result')
    else:
        print(f[0][0])
        last_f = f

    for iChannel in src.channel_ids:
       d[:, iChannel] = d[:, iChannel] + (1 * (iChannel + 1))

    ax1.clear()
    ax1.plot(d[:, 0:8])
    # plt.ylim((0, 12))
    plt.xlabel('Samples')
    plt.ylabel('Channel')
    plt.title('EMG Stream')
    # print('{:0.2f}'.format(m.get_data_rate_emg()))


ani = animation.FuncAnimation(fig, animate, interval=150)
plt.show()

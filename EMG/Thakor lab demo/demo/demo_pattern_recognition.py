import argparse

import numpy as np

from scipy.io import loadmat

from MyoArmband import MyoArmband
from TimeDomainFilter import TimeDomainFilter
from LinearDiscriminantAnalysis import LinearDiscriminantAnalysis
from UniformVoteFilter import UniformVoteFilter

DEVICE = [ 'myo' ][0]
CLASSES = [ 'rest', 'power', 'open', 'pronate', 'supinate' ]

if __name__ == '__main__':
    def cmdline( arg ):
	    return arg[0] if type( arg ) is list else arg
    # parse commandline entries
    parser = argparse.ArgumentParser()
    parser.add_argument( '--mac', type = str, nargs = '+', action = 'store', dest = 'myo_mac', default = 'eb:33:40:96:ce:a5' )
    parser.add_argument( '--emg_window_size', type = int, nargs = '+', action = 'store', dest = 'emg_window_size', default = 50 )
    parser.add_argument( '--emg_window_step', type = int, nargs = '+', action = 'store', dest = 'emg_window_step', default = 10 )
    parser.add_argument( '--training_file', type = str, nargs = '+', action = 'store', dest = 'training_file', default = 'train.mat' )

    args = parser.parse_args()

    # command-line parameters
    mac = cmdline( args.myo_mac )
    emg_window_size = cmdline( args.emg_window_size )
    emg_window_step = cmdline( args.emg_window_step )
    bb3_mac = cmdline( args.bb3_mac )
    training_file = cmdline( args.training_file )

    # download training data
    print( 'Importing training data...', end = '', flush = True)
    training_data = loadmat( training_file )['train'][0]
    print( 'Done!' )

    # create feature extracting filters
    print( 'Creating EMG feature filters...', end = '', flush = True )
    td5 = TimeDomainFilter()
    print( 'Done!' )

    # compute training features and labels
    print( 'Computing features...', end = '', flush = True)
    num_trials = len( training_data )
    X = []
    y = []
    for i in range( len( CLASSES ) ):
        class_data = []
        for j in range( num_trials ):
            raw_data = training_data[ j ][ CLASSES[ i ] ][0][0]
            num_samples = raw_data.shape[0]
            idx = 0
            while idx + emg_window_size < num_samples:
                window = raw_data[idx:(idx+emg_window_size),:]
                time_domain = td5.filter( window ).flatten()
                class_data.append( np.hstack( time_domain ) )
                idx += emg_window_step
        X.append( np.vstack( class_data ) )
        y.append( i * np.ones( ( X[-1].shape[0], ) ) )
    X = np.vstack( X )
    y = np.hstack( y )
    print( 'Done!' )

    # train classifier
    print( 'Training LDA classifier...', end = '', flush = True )
    mdl = LinearDiscriminantAnalysis( X, y )
    print( 'Done!' )

    print( 'Creating output filters...', end = '', flush = True )
    uni = UniformVoteFilter( size = 5 )
    print( 'Done!' )

    # create Myo interface
    print( 'Creating device interface...', end = '', flush = True )
    myo = MyoArmband( mac = mac )
    print( 'Done!' )

    print( 'Starting data streaming...', end = '\n', flush = True )
    myo.run()
    try:
        emg_window = []
        myo.flush()
        while True:
            data = myo.state
            if data is not None:
                emg_window.append( data[:8] )
                if len( emg_window ) == emg_window_size:
                    win = np.vstack( emg_window )
                    feat = td5.filter( win )
                    
                    pred = int( mdl.predict( feat.reshape( 1, -1 ) )[0] )
                    out = uni.filter( pred )

                    print( pred, out )
                    print( 'CLASSIFIER OUTPUT: %s' % ( CLASSES[out] ).upper() )

                    emg_window = emg_window[emg_window_step:]
    finally:
        myo.stop()
        myo.close()

    print( 'Done!' )
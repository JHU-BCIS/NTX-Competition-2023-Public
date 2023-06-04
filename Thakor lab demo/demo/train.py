import argparse

import time

import numpy as np

import matplotlib
matplotlib.use( 'QT5Agg')

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from scipy.io import savemat

from MyoArmband import MyoArmband

DEVICE = [ 'myo' ][0]

if __name__ == '__main__':
    # helper function to clean commandline input
    def cmdline( arg ):
        return arg[0] if type( arg ) is list else arg

    # parse commandline entries
    parser = argparse.ArgumentParser()

    parser.add_argument( '--num_trials', type = int, nargs = '+', action = 'store', dest = 'num_trials', default = 1 )
    parser.add_argument( '--cue_delay', type = int, nargs = '+', action = 'store', dest = 'cue_delay', default = 2 )
    parser.add_argument( '--cue_duration', type = int, nargs = '+', action = 'store', dest = 'cue_duration', default = 3 )

    parser.add_argument( '--name', type = str, nargs = '+', action = 'store', dest = 'name', default = 'MyoArmband' )
    parser.add_argument( '--mac', type = str, nargs = '+', action = 'store', dest = 'mac', default = 'eb:33:40:96:ce:a5' )

    args = parser.parse_args()

    # command-line parameters
    num_trials = cmdline( args.num_trials )
    cue_delay = cmdline( args.cue_delay )
    cue_duration = cmdline( args.cue_duration )
    name = cmdline( args.name )
    mac = cmdline( args.mac )
    if DEVICE == 'sense':
        num_electrodes = cmdline( args.num_electrodes )
        gain = cmdline( args.gain )
    elif DEVICE == 'myo':
        num_electrodes = 8

    CUE_LIST = [ 'rest', 'power', 'open', 'pronate', 'supinate' ]

    # download cue images
    #print( 'Importing cue images...', end = '', flush = True )
    #cue_images = {}
    #for cue in CUE_LIST:
    #    img = mpimg.imread( 'cues/' + cue + '.png' )
    #    cue_images.update( { cue : img } )
    #print( 'Done!' )

    # create Myo interface
    print( 'Creating device interface...', end = '', flush = True )
    myo = MyoArmband( name = name, mac = mac )
    print( 'Done!' )

    print( 'Starting data collection...', end = '\n', flush = True )
    myo.run()
    try:
        train = np.zeros( ( num_trials, ), dtype = np.object ) # training data

        # cue_fig = plt.figure()
        # plt.ion()
        for trial in range( num_trials ):
            train[ trial ] = {}
            for cue in CUE_LIST: 
                train[ trial ].update( { cue : [] } )
        
            print( '\tTrial %02d...' % ( trial+1 ) )
            # random.shuffle( CUE_LIST )
            for cue in CUE_LIST:
                print( '\t\t%s...' % cue.upper(), end = '\t' )
                
                # set up the cue image
                # plt.imshow( cue_images[ cue ] )
                # plt.axis( 'off' )
                # plt.show( block = False )

                # wait through the delay
                t0 = time.perf_counter()
                while( time.perf_counter() - t0 ) < cue_delay:
                    # cue_fig.canvas.flush_events()
                    while myo.state is not None: 
                        pass

                # collect data for the duration
                cue_data = []
                t0 = time.perf_counter()
                while ( time.perf_counter() - t0 ) < cue_duration:
                    data = myo.state
                    if data is not None:
                        cue_data.append( data[:num_electrodes].copy() )

                train[ trial ][ cue ] = np.vstack( cue_data )
                print( train[ trial ][ cue ].shape )
    finally:
        myo.stop()
        myo.close()

    print( 'Saving data...', end = '', flush = True )
    savemat( 'train.mat', mdict = { 'train' : train } )
    print( 'Done!' )
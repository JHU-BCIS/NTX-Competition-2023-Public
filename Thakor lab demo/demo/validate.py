# imports
import argparse
import itertools
import numpy as np

import matplotlib as mpl
mpl.use( 'QT5Agg' )
import matplotlib.pyplot as plt
from mpl_toolkits import axes_grid1

from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix as sk_confusion_matrix
from scipy.io import loadmat

from TimeDomainFilter import TimeDomainFilter
from LinearDiscriminantAnalysis import LinearDiscriminantAnalysis

DEVICE = [ 'myo' ][0]

# parameters
parser = argparse.ArgumentParser()

parser.add_argument( '--emg_window_size', type = int, nargs = '+', action = 'store', dest = 'emg_window_size', default =  50 )
parser.add_argument( '--emg_window_step', type = int, nargs = '+', action = 'store', dest = 'emg_window_step', default = 10 )
parser.add_argument( '--training_file', type = str, nargs = '+', action = 'store', dest = 'training_file', default = 'train.mat' )

args = parser.parse_args()

# command-line parameters
emg_window_size = args.emg_window_size[0] if type( args.emg_window_size ) is list else args.emg_window_size
emg_window_step = args.emg_window_step[0] if type( args.emg_window_step ) is list else args.emg_window_step
training_file = args.training_file[0] if type( args.training_file ) is list else args.training_file

CLASSES = [ 'rest', 'power', 'open', 'pronate', 'supinate' ]

# function definitions

def confusion_matrix( ytest, yhat, labels = [], cmap = 'viridis', ax = None, show = True ):
    """
    Computes (and displays) a confusion matrix given true and predicted classification labels

    Parameters
    ----------
    ytest : numpy.ndarray (n_samples,)
        The true labels
    yhat : numpy.ndarray (n_samples,)
        The predicted label
    labels : iterable
        The class labels
    cmap : str
        The colormap for the confusion matrix
    ax : axis or None
        A pre-instantiated axis to plot the confusion matrix on
    show : bool
        A flag determining whether we should plot the confusion matrix (True) or not (False)

    Returns
    -------
    numpy.ndarray
        The confusion matrix numerical values [n_classes x n_classes]
    axis
        The graphic axis that the confusion matrix is plotted on or None

    """
    def add_colorbar(im, aspect=20, pad_fraction=0.5, **kwargs):
        """Add a vertical color bar to an image plot."""
        divider = axes_grid1.make_axes_locatable(im.axes)
        width = axes_grid1.axes_size.AxesY(im.axes, aspect=1./aspect)
        pad = axes_grid1.axes_size.Fraction(pad_fraction, width)
        current_ax = plt.gca()
        cax = divider.append_axes("right", size=width, pad=pad)
        plt.sca(current_ax)
        return im.axes.figure.colorbar(im, cax=cax, **kwargs)

    cm = sk_confusion_matrix( ytest, yhat )
    cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    if ax is None:    
        fig = plt.figure()
        ax = fig.add_subplot( 111 )

    try:
        plt.set_cmap( cmap )
    except ValueError: cmap = 'viridis'

    im = ax.imshow( cm, interpolation = 'nearest', vmin = 0.0, vmax = 1.0, cmap = cmap )
    add_colorbar( im )

    if len( labels ):
        tick_marks = np.arange( len( labels ) )
        plt.xticks( tick_marks, labels, rotation=45 )
        plt.yticks( tick_marks, labels )

    thresh = 0.5 # cm.max() / 2.
    colors = mpl.cm.get_cmap( cmap )
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        r,g,b,_ = colors(cm[i,j])
        br = np.sqrt( r*r*0.241 + g*g*0.691 + b*b*0.068 )
        plt.text(j, i, format(cm[i, j], '.2f'),
                    horizontalalignment = "center",
                    verticalalignment = 'center',
                    color = "black" if br > thresh else "white")

    plt.ylabel('Actual')
    plt.xlabel('Predicted')

    ax.set_ylim( cm.shape[0] - 0.5, -0.5 )
    plt.tight_layout()
    if show: plt.show( block = True )
    
    return cm, ax

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

# split data
print( 'Computing train/test split...', end = '', flush = True )
Xtrain, Xtest, ytrain, ytest = train_test_split( X, y, test_size = 0.33 )
print( 'Done!' )

# train classifier
print( 'Training classifier...', end = '', flush = True )
mdl = LinearDiscriminantAnalysis( Xtrain, ytrain )
print( 'Done!' )

# test classifier
print( 'Testing classifier...', end = '', flush = True )
yhat = mdl.predict( Xtest )
print( 'Done!' )

print( yhat - ytest )

# show results
fig = plt.figure( figsize = (10.0, 5.0) )
ax = fig.add_subplot( 111 )

cm, _ = confusion_matrix( ytest, yhat, labels = CLASSES, ax = ax, show = False )
ax.set_title( 'LDA Classification' )

print( '\nAVERAGE CLASSIFICATION ACCURACY: %0.2f' % np.mean( np.diag( cm ) ) )

plt.tight_layout()
plt.show()
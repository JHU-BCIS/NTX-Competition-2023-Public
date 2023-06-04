class UniformVoteFilter:
    """ A Python implementation of a uniform vote output filter """
    def __init__( self, size = 3 ):
        """
        Constructor

        Parameters
        ----------
        size : int
            The length of the output filter

        Returns
        -------
        obj
            A UniformVoteFilter object
        """
        self.__size = size
        self.__buffer = [ -1 ] * self.__size

    def filter( self, pred ):
        """
        """
        self.__buffer = self.__buffer[1:] + [ pred ]    # circular buffer
        if self.__buffer[1:] == self.__buffer[:-1]:     # all elements in buffer are the same
            return pred
        else:
            return 0

    def reset( self ):
        """
        """
        self.__buffer = [ -1 ] * self.__size

if __name__ == '__main__':
    N_CLASSES = 7
    UNIFORM_SIZE = 3

    predictions = []
    for i in range( N_CLASSES ):
        predictions.extend( [ i ] * UNIFORM_SIZE )

    output = []
    uniform = UniformVoteFilter( size = UNIFORM_SIZE )
    for pred in predictions:
        output.append( uniform.filter( pred ) )

    print( 'Predictions:', predictions )
    print( 'Output:     ', output )
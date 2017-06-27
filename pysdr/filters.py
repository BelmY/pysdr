# The point of these filters is not to "implement filters" per se, it's to use existing implementations of filters
#    but provide them in a "streaming" manner, where batches of samples go through them without the developer
#    having to worry about discontinuities and such.  

import numpy as np
import time
from scipy import signal
import matplotlib.pyplot as plt

# a np.convolve based filter, similar to signal.lfilter() but 6x faster even though it's still python
class fir_filter:
    def __init__(self, taps):
        self.taps = taps
        self.previous_batch = np.zeros(len(self.taps) - 1, dtype=np.complex128) # holds end of previous batch, this is the "state" essentially

    def filter(self, x):
        out = np.convolve(np.concatenate((self.previous_batch, x)), self.taps, mode='valid')
        self.previous_batch[-min((len(self.taps) - 1), len(x)):] = x[-min((len(self.taps) - 1), len(x)):] # the last portion of the batch gets saved for the next iteration #FIXME if batches become smaller than taps this won't work
        return out

# an fft based filter (currently sux)
class fft_filter:
    def __init__(self, taps):
        self.taps = taps
        self.previous_batch = np.zeros(len(self.taps) - 1, dtype=np.complex128) # holds end of previous batch, this is the "state" essentially
    def filter(self, x):
        out = signal.fftconvolve(np.concatenate((self.previous_batch, x)), self.taps, mode='valid')
        self.previous_batch[-min((len(self.taps) - 1), len(x)):] = x[-min((len(self.taps) - 1), len(x)):] # the last portion of the batch gets saved for the next iteration #FIXME if batches become smaller than taps this won't work
        return out


##############
# UNIT TESTS # 
##############
if __name__ == '__main__': # (call this script directly to run tests)
    x = np.random.randn(100) + 1j*np.random.randn(100) # signal
    taps = np.random.rand(10)

    # simple method of filtering
    y = np.convolve(x, taps, mode='valid')

    # now using the various stream-based FIR filters
    y2 = np.zeros(0) # fir_filter
    y3 = np.zeros(0) # fft_filter
    y4 = np.zeros(0) # scipy's lfilter
    batch_size = 7 # represents how many samples come in at the same time
    test_filter = fir_filter(taps) # initialize filters
    test_filter2 = fft_filter(taps)
    zi = np.zeros(len(taps) - 1) # used for lfilter
    for i in range(len(x)/batch_size):
        x_input = x[i*batch_size:(i+1)*batch_size] # this line represents the incoming stream
        filter_output = test_filter.filter(x_input) # run the filter
        y2 = np.concatenate((y2, filter_output)) # add output to our log
        filter_output = test_filter2.filter(x_input) 
        y3 = np.concatenate((y3, filter_output))
        #start = time.time()
        filter_output, zi = signal.lfilter(taps, [1], x_input, zi=zi)
        #print 'It took', time.time()-start, 'seconds.'
        y4 = np.concatenate((y4, filter_output))
    # get rid of the beginning that was computed using zeros, in order to make it equal to simple method (this wont matter in real apps, its just a transient thing)
    y2 = y2[len(taps)-1:]
    y3 = y3[len(taps)-1:] 
    y4 = y4[len(taps)-1:] 
    # if taps were longer than batch size, we have to get rid of the extra part of y
    if len(taps) > batch_size:
        y = y[:-(len(taps) - batch_size - 1)]
    plt.plot(y2-y)
    plt.show()
    print "fir_filter test passed? ", np.allclose(y, y2, rtol=1e-10) 
    print "fft_filter test passed? ", np.allclose(y, y3, rtol=1e-10) 
    print "lfilter test passed? ",    np.allclose(y, y4, rtol=1e-10) 
    


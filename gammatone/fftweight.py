# Copyright 2014 Jason Heeris, jason.heeris@gmail.com
# 
# This file is part of the gammatone toolkit, and is licensed under the 3-clause
# BSD license: https://github.com/detly/gammatone/blob/master/COPYING
"""
This module contains functions for calculating weights to approximate a
gammatone filterbank-like "spectrogram" from a Fourier transform.
"""
import numpy as np

from . import filters


def fft_weights(
    nfft,
    fs,
    nfilts,
    width,
    fmin,
    fmax,
    maxlen):
    """
    :param nfft: the source FFT size
    :param sr: sampling rate (Hz)
    :param nfilts: the number of output bands required (default 64)
    :param width: the constant width of each band in Bark (default 1)
    :param fmin: lower limit of frequencies (Hz)
    :param fmax: upper limit of frequencies (Hz)
    :param maxlen: number of bins to truncate the rows to
    
    :return: a tuple `weights`, `gain` with the calculated weight matrices and
             gain vectors
    
    Generate a matrix of weights to combine FFT bins into Gammatone bins.
    
    Note about `maxlen` parameter: While wts has nfft columns, the second half
    are all zero. Hence, aud spectrum is::
    
        fft2gammatonemx(nfft,sr)*abs(fft(xincols,nfft))
    
    `maxlen` truncates the rows to this many bins.
    
    | (c) 2004-2009 Dan Ellis dpwe@ee.columbia.edu  based on rastamat/audspec.m
    | (c) 2012 Jason Heeris (Python implementation)
    """
    ucirc_range = nfft/2 + 1
    ucirc = np.exp(1j*2*np.pi*np.arange(0, ucirc_range)/nfft)[None, ...]
    
    # Common ERB filter code factored out
    cf_array = filters.erb_space(fmin, fmax, nfilts)
    cf_array = cf_array[::-1]

    _, A11, A12, A13, A14, _, _, _, B2, gain = (
        filters.make_erb_filters(fs, cf_array, width).T
    )
    
    A11, A12, A13, A14 = A11[..., None], A12[..., None], A13[..., None], A14[..., None]

    r = np.sqrt(B2)
    theta = 2*np.pi*cf_array/fs    
    pole = (r*np.exp(1j*theta))[..., None]
    
    GTord = 4
    
    weights = np.zeros((nfilts, nfft))
    
    weights[:, 0:ucirc_range] = (
          np.abs(ucirc + A11 * fs) * np.abs(ucirc + A12 * fs)
        * np.abs(ucirc + A13 * fs) * np.abs(ucirc + A14 * fs)
        * np.abs(fs * (pole - ucirc) * (pole.conj() - ucirc)) ** (-GTord)
        / gain[..., None]
    )

    weights = weights[:, 0:maxlen]

    return weights, gain
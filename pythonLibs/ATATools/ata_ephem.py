#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from ATATools import ata_control, logger_defaults
import atexit
from SNAPobs import snap_dada, snap_if
import numpy as np
import sys
import time

import argparse
import logging

import os


def generate_ephem_el_swivel(az_start, el_start, el_end, t_start, t_span,  steps, invr):
    """
    Swivel along Elevation

    This function creates an ephemeris array to enable the antennas to swivel 
    across elevation at a particular azimuth

    Parameters 
    ----------
    az_start : float
               azimuth start
    el_start : float
               elevation start
    el_end   : float
               elevation end
    t_start  : float
               start time of the swivel. Note that it will be in ATA TAI seconds
    t_span   : float
               time span of the swivel in seconds
    steps    : float
               Number of data points required
    invr    :  float
               Inverse radius of the source

    Returns
    -------
    ephem : numpy_array
            Returns an array with 4 columns for time in TAI ns, azimuth, elevation 
            and inverse radius of the source
                
    Note
    ----
    ATA TAI is 37 seconds ahead of the current time

    """
    tai = np.linspace(t_start*1e9, (t_start + t_span)*1e9, steps)

    tai = np.round(tai).astype('int')

    el = np.linspace(el_start, el_end, steps)
    
    ir = np.array(steps*[invr])
    
    az = np.array(steps*[az_start])

    ephem = ((np.array([tai, az, el, ir], dtype=object)))
    
    return(ephem.T)



def generate_ephem_az_swivel(az_start, az_end, el_start, t_start, t_span,  steps, invr):
    """
    Swivel along Azimuth

    This function creates an ephemeris array to enable the antennas to swivel 
    across azimuth at a particular elevation

    Parameters 
    ----------
    az_start : float
               azimuth start
    az_end   : float
               azimuth end
    el_start : float
               elevation start
    t_start  : float
               start time of the swivel. Note that it will be in ATA TAI seconds
    t_span   : float
               time span of the swivel in seconds
    steps    : float
               Number of data points required
    invr    :  float
               Inverse radius of the source

    Returns
    -------
    ephem : numpy_array
            Returns an array with 4 columns for time in TAI ns, azimuth, elevation 
            and inverse radius of the source
                
    Note
    ----
    ATA TAI is 37 seconds ahead of the current time

    """
    tai = np.linspace(t_start*1e9, (t_start + t_span)*1e9, steps)

    tai = np.round(tai).astype('int')

    az = np.linspace(az_start, az_end, steps)
    
    ir = np.array(steps*[invr])
    
    el = np.array(steps*[el_start])

    ephem = ((np.array([tai, az, el, ir], dtype=object)))
    
    return(ephem.T)




def ephem_to_txt(save_as, ephem_file):
    """
    Ephemeris to text file

    This function exports the ephemeris array to a txt file

    Parameters
    ----------
    save_as    : string
                 file name to save the array as
    ephem_file : array
                 the ephemeris array to be exported as a txt file

    """
    ephemtxt = np.savetxt(save_as, ephem_file, fmt='%i  %.5f  %.5f  %.10E')

    return(ephemtxt)





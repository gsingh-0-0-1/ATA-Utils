#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tools to auto tune the PAMs

Created Jan 2020

@author: jkulpa
"""



import sys

import numpy
import logging
import re
import ATASQL
from mysql.connector import Error 


defaultAntenna = '1c'
validAntennas = ['1a','1b','1c','1d','1e','1f', '1g', '1h', '1j', '1k', '2a', '2b',
                 '2c', '2d', '2e', '2f', '2g', '2h', '2j', '2k', '2l', '2m', '3c',
                 '3d', '3e', '3f', '3g', '3h', '3j', '3l', '4e', '4f', '4g', '4h',
                 '4j', '4k', '4l', '5b', '5c', '5e', '5g', '5h']

def getPolynomials(alist):
    """
    Function return 
    
    input: alist - list of antennas. must in short format, i.e. ['1a','1b']
    returns: antpol dictionary of polynomials, lower and upper bound 
    """
    
    
    logger = logging.getLogger(__name__)
    logger.info("connecting to database")
    
    mydb = ATASQL.connectATAROnly()
    cursor = mydb.cursor()
    
    queryPart = ("select feed_parts.ant,pbmeas.pax_box_sn,pbmeas.pol,pbmeas.iscoherent,pbmeas.lowdet,pbmeas.highdet,pbmeas.p0,pbmeas.p1,pbmeas.p2,pbmeas.p3,pbmeas.p4,pbmeas.p5 "
                 "from (pbmeas inner join feed_parts on pbmeas.pax_box_sn = feed_parts.pax_box_sn) where pbmeas.type='cw' "
                 "and feed_parts.ant in (%s);")
    
    
    in_p=', '.join(map(lambda x: '%s', alist))
    query = queryPart % in_p;
    cursor.execute(query, alist)
    
    #getting the values from the database. Only measured antennas would be returned here
    antennasgot = {}
    polydict={}
    lowerdict = {}
    upperdict = {}
    for (ant,sn,pol,isc,low,high,p0,p1,p2,p3,p4,p5) in cursor:
        antennasgot[ant] = 1
        antpol = ant + pol;
        polydict[antpol] = numpy.poly1d([p5,p4,p3,p2,p1,p0]);
        lowerdict[antpol] = low;
        upperdict[antpol] = high;
        if not isc:
          logger.warning("antenna's " + ant + pol + " pambox is marked for uncertain measurement")
    
    #checking if both polarizations are there. 
    for ant in antennasgot:
        if not ant + 'x' in polydict or not ant + 'y' in polydict:
            logger.warning("missing polarization for "  + ant)
            raise KeyError("missing polarization for "  + ant)
            
    #we need to see if we have all data gathered
    missingAnts = list(set(alist) - set(antennasgot))
    
    if missingAnts:
        logger.info("we are missing following antennas %s" % missingAnts)
        #we have some missing ants. lets check if we have already downloaded the default Antenna
        if defaultAntenna in antennasgot:
            for ant in missingAnts:
                polydict[ant + 'x'] = polydict[defaultAntenna + 'x'] 
                lowerdict[ant + 'x'] = lowerdict[defaultAntenna + 'x']
                upperdict[ant + 'x'] = upperdict[defaultAntenna + 'x']
                polydict[ant + 'y'] = polydict[defaultAntenna + 'y'] 
                lowerdict[ant + 'y'] = lowerdict[defaultAntenna + 'y']
                upperdict[ant + 'y'] = upperdict[defaultAntenna + 'y']
        else:
            logger.info("no default antenna in the set, quering default: %s" % defaultAntenna)
            #next querry to get default antenna data
            in_p = '%s'
            query = queryPart % in_p;
            cursor.execute(query, [defaultAntenna])
            defaultdictpoly = {}
            defaultdictlower = {}
            defaultdictupper = {}
            for (ant,sn,pol,isc,low,high,p0,p1,p2,p3,p4,p5) in cursor:
                antpol = ant + pol;
                defaultdictpoly[antpol] = numpy.poly1d([p5,p4,p3,p2,p1,p0]);
                defaultdictlower[antpol] = low;
                defaultdictupper[antpol] = high;
            
            #do we have both polarization of default one?
            if not defaultAntenna + 'x' in defaultdictpoly or not defaultAntenna + 'y' in defaultdictpoly:
                logger.warning("missing polarization for "  + defaultAntenna)
                raise KeyError("missing polarization for "  + defaultAntenna)
                
            #now we have a new dictionary, we may fill the remaining parts
            for ant in missingAnts:
                polydict[ant + 'x'] = defaultdictpoly[defaultAntenna + 'x'] 
                lowerdict[ant + 'x'] = defaultdictlower[defaultAntenna + 'x']
                upperdict[ant + 'x'] = defaultdictupper[defaultAntenna + 'x']
                polydict[ant + 'y'] = defaultdictpoly[defaultAntenna + 'y'] 
                lowerdict[ant + 'y'] = defaultdictlower[defaultAntenna + 'y']
                upperdict[ant + 'y'] = defaultdictupper[defaultAntenna + 'y']
            
    return polydict,lowerdict,upperdict,missingAnts;
    

#select feed_parts.ant,pbmeas.pax_box_sn,pbmeas.pol,pbmeas.iscoherent,pbmeas.lowdet,pbmeas.highdet,pbmeas.p0,pbmeas.p1,pbmeas.p2,pbmeas.p3,pbmeas.p4,pbmeas.p5 from (pbmeas inner join feed_parts on pbmeas.pax_box_sn = feed_parts.pax_box_sn) where pbmeas.type='cw' and feed_parts.ant in ('3c');

def checkIfValidAntenna(antennalist):
    for ant in antennalist:
        if ant not in validAntennas:
            logger = logging.getLogger(__name__)
            logger.warning('Antenna ' + ant + ' is not a valid antenna name')
            raise KeyError('Antenna ' + ant + ' is not a valid antenna name')

def cleanAntennaString(antstring):
    antstringout = re.sub(r'ant', '', antstring)
    #print(antstring)
    #print(antstringout)
    return antstringout

def splitAntennaString(antstring):
    antenna = antstring.split(',')
    checkIfValidAntenna(antenna)
    return antenna


def getAntennas(arg):
  """
  clear and uniform the antenna string. check if antenna exist. 
  
  Parameters
  -------------
  arg : str
      comma separated list of antenna names, both long and short may be mixed
        
  Returns
  -------------
  str
      string of short antenna names
  list 
      list of short antenna names
        
  Raises
  -------------
      KeyError (antenna not on the list)
  """
  antstr = cleanAntennaString(arg);
  antlist = splitAntennaString(antstr);
  return antstr,antlist





'''
Created on Feb 1, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
from skip.collection import NamedElementCollection
from skip.sexp.parser import ParsedValue, ParsedValueWrapper



class NetWrapper(ParsedValueWrapper):
    '''
        A net -- connection nodes.  Has an id and a name
        >>> n
        <Net 99 /RP2040/QSPI_SD2>
        >>> n.id
        99
        >>> n.name
        '/RP2040/QSPI_SD2'
        
        
        It may have been access from the nets list on the PCB,
        or indirectly, from some other object, e.g.
        
        >>> segment
        <Segment in /vfused on F.Cu>
        >>> segment.net
        <Net 113 /vfused>
        >>> seg.net == pcb.net.vfused
        True
        
        # get all the segments in this net
        >>> list(filter(lambda seg: seg.net == pcb.net.vfused, pcb.segment))
        [<Segment in /vfused on F.Cu>, <Segment in /vfused on F.Cu>, <Segment in /vfused on F.Cu>]


    '''
    def __init__(self, v:ParsedValue):
        super().__init__(v)
        self._id = v.value[0]
        self._name = v.value[1]
    
    @property 
    def id(self):
        return self._id 
    
    @property 
    def name(self):
        return self._name 
    
    def __repr__(self):
        return f'<Net {self.id} {self.name}>'
        

class NetCollection(NamedElementCollection):
    '''
       A collection of all the nets.
       
       The actual nets within are accessible:
       
        * as attributes (using names that may be munged a bit, for python's sake)
          
         nets.HK_CSB
         nets.HK_SCK
         nets.HK_SDI
         nets.HK_SDO
         nets.P1V8  
         nets.P3V3  
         nets.P5V
         nets.unnamed_C3_Pad1
         nets.unnamed_D1_A
         (actual names depend on schem)
         
        * as indexed by their name or their id
        
        >>> nets[25]
        <Net 25 HK_SCK>
        >>> nets['HK_SCK']
        <Net 25 HK_SCK>
        
        


    '''
    NetDropFirsSlashRegex = re.compile(r'^/')
    NetDropCharsRegex = re.compile(r'[}{\)\(]+')
    NetNameCleanerRegex = re.compile(r'[^\w\d_]')
    NetUnlabeledRegex = re.compile(r'^Net-')
    
    @classmethod
    def cleanNetName(cls, v:str):
        if v is None or not len(v):
            return '_X'
        
        v = v.replace('~', 'n')
        v = v.replace('+', 'P')
        v = cls.NetDropFirsSlashRegex.sub('', v)
        v = cls.NetDropCharsRegex.sub('', v)
        v = cls.NetUnlabeledRegex.sub('unnamed_', v)
        v = cls.NetNameCleanerRegex.sub('_', v)
        return v
    
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements, lambda nt: NetCollection.cleanNetName(nt.value[1]))
        

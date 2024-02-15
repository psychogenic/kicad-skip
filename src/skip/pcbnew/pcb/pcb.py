'''
Main handle to kicad schematic.

This is the top level object for all the action in this library.  If you



Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from skip.sexp.sourcefile import SourceFile
from skip.pcbnew.layer import  LayersListWrapper
from skip.pcbnew.net import NetCollection, NetWrapper
from skip.pcbnew.segment import SegmentWrapper
from skip.pcbnew.footprint import FootprintWrapper, FootprintCollection
from skip.pcbnew.graphical import GraphicalElementWrapper, TextElementWrapper, PolygonWrapper
import logging 
log = logging.getLogger(__name__)

class PCB(SourceFile):
    '''
        Main handle to kicad PCBs
        
        import skip
        pcb = skip.PCB('path/to/file.kicad_pcb')
        
        
        then pcb will hold a number of attributes, which depend on the contents
        of the layout.
        
        
        *DO* use a console and TAB-completion to explore the object.
        
        pcb.<TAB><TAB>  will show a number of members.  
        Some of most interest are likely
        
        
        '''
    def __init__(self, filepath:str):
        '''
            c'tor for the schematic object, gateway to everything in the 
            kicad_sch file.
            
            @param filepath: path/to/schematic.kicad_sch
            
            This is the main handle to a schematic sheet.
            
            @note: No checking is done at all.  If the file DNE, it dies.  
            If it's not a kicad schematic... who knows.
        '''
        super().__init__(filepath)
    
    
    
    def dedicated_collection_type_for(self, entity_type:str):
        dedicatedCollection = {
        
            #'layers': LayerCollection
            'footprint': FootprintCollection,
            'net': NetCollection
        }
        if entity_type in dedicatedCollection:
            return dedicatedCollection[entity_type]
        return None 
    def dedicated_wrapper_type_for(self, entity_type:str):
        
        dedicatedWrapper = {
            'layers': LayersListWrapper, # yeah, weird: one element that's a list for some reason
            'net': NetWrapper,
            'segment': SegmentWrapper,
            'footprint': FootprintWrapper,
            
            # gr_*
            'gr_text': TextElementWrapper,
            'gr_arc': GraphicalElementWrapper,
            'gr_circle': GraphicalElementWrapper,
            'gr_line': GraphicalElementWrapper,
            'gr_poly': PolygonWrapper,
            'gr_rect': GraphicalElementWrapper,
        }
        if entity_type in dedicatedWrapper:
            return dedicatedWrapper[entity_type]
        
        return None 
    
    def __repr__(self):
        return f"<PCB '{self._filepath}'>"



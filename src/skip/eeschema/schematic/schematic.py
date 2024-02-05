'''
Main handle to kicad schematic.

This is the top level object for all the action in this library.  If you



Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from skip.sexp.sourcefile import SourceFile
from skip.eeschema.schematic.symbol import SymbolCollection, Symbol
from skip.eeschema.sheet.sheet import SheetWrapper
from skip.eeschema.lib_symbol import LibSymbolsListWrapper
from skip.eeschema.wire import WireCollection, WireWrapper
from skip.eeschema.label import LabelCollection, LabelWrapper
from skip.eeschema.label import GlobalLabelCollection, GlobalLabelWrapper
from skip.eeschema.text import TextCollection, TextWrapper
from skip.eeschema.junction import JunctionCollection, JunctionWrapper
import logging 
log = logging.getLogger(__name__)

class Schematic(SourceFile):
    '''
        Main handle to kicad schematics
        
        import skip
        sch = skip.Schematic('path/to/file.kicad_sch')
        
        
        then sch will hold a number of attributes, which depend on the contents
        of the schematic.
        
        
        *DO* use a console and TAB-completion to explore the object.
        
        sch.<TAB><TAB>  will show a number of members.  
        Some of most interest are likely
        
        
          sch.symbol
          sch.title_block
          sch.text
        
        but you'll also probably find
        
        sch.wire
        sch.label
        sch.junction
        sch.rectangle
        and more.
        
        Each attribute will either be:
          * an object 
          * a basic list of objects
          * a collection of objects
        
        Dedicated collections are used in some instances.  These can act just like lists
        
        for component in sch.symbol:
            print(f'Setting datasheet and DNP on {component.property.Reference.value}')
            component.property.Datasheet.value = 'Ho.pdf'
            component.dnp = True
        
        But often also as objects with attributes. For symbols (components) these are the
        reference of the component, which is very useful when operating in a console.
        
        Use tab-completion to see them all
        
        sch.symbol.<TAB><TAB>
        
        and use 'em.
        sch.symbol.C42.dnp = True
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
    
    @classmethod
    def dedicated_collections_by_type(cls):
        return {
        
            'symbol': SymbolCollection,
            'wire': WireCollection,
            'label': LabelCollection,
            'global_label': GlobalLabelCollection,
            'text': TextCollection,
            'junction': JunctionCollection
        }
    
    
    @classmethod 
    def dedicated_wrapper_type_for(cls, entity_type:str):
        
        dedicatedWrapper = {
            'symbol': Symbol,
            'sheet': SheetWrapper,
            'lib_symbols': LibSymbolsListWrapper, # this single element acts like a list (children)
            'wire': WireWrapper,
            'label': LabelWrapper,
            'global_label': GlobalLabelWrapper,
            'text': TextWrapper,
            'junction': JunctionWrapper
        }
        if entity_type in dedicatedWrapper:
            return dedicatedWrapper[entity_type]
        
        return None 
    
    
    
    
    
    def _searchable_collections(self):
        possible_collections = ['symbol', 'label', 'global_label']
        colls = []
        for pc in possible_collections:
            if hasattr(self, pc):
                colls.append(getattr(self, pc))
        
        return colls
    
    
    def within_reach_of(self, element, distance:float):
        '''    
            Find all elements of this collection that are within 
            reach of passed element.
            
            @param element: element in question, must have .at or .location
            
            @param distance: maximal distance, in coord units  
            
            @note: only works for elements that have a
            suitable 'at' or 'location' attribute
        
        '''
        retvals = []
        for col in self._searchable_collections():
            retvals.extend(col.within_reach_of(element, distance))
        return retvals
            
    def within_rectangle(self, x1coord:float, y1coord:float, x2coord:float, y2coord:float):
        '''
            Find all elements of this collection that are within the 
            rectangle bounded by (x1,y1) - (x2,y2)
        '''
        
        retvals = []
        for col in self._searchable_collections():
            retvals.extend(col.within_rectangle(x1coord, y1coord, x2coord, y2coord))
        return retvals
    
    
    def within_circle(self, xcoord:float, ycoord:float, radius:float):
        '''    
            Find all elements of this collection that are within the 
            circle of radius radius, centered on xcoord, ycoord.
            
            @note: only works for elements that have a
            suitable 'at' or 'location' attribute
        
        '''
        retvals = []
        for col in self._searchable_collections():
            retvals.extend(col.within_circle(xcoord, ycoord, radius))
        return retvals
            
    def between_elements(self, positionedElement1, positionedElement2):
        '''
            return a list of all elements, between these two, i.e. located 
            in the rectangle comprised by each of their locations.
            
            @param positionedElement1: some parsed value with an 'at' or 'location' 
            @param positionedElement2: some parsed value with an 'at' or 'location' 
        '''
        
        retvals = []
        for col in self._searchable_collections():
            retvals.extend(col.between_elements(positionedElement1, positionedElement2))
        return retvals
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def __str__(self):
        if hasattr(self,'title_block'):
            return f"{self.__repr__()}\n{str(self.title_block)}"
        return self.__repr__()
    def __repr__(self):
        return f"<Schematic '{self._filepath}'>"



def DNPAll(s:Schematic, donotpopulate:bool=True):
    count = 0
    for k,c in s.symbols_by_name.items():
        if k.startswith('#'):
            continue 
        log.info(f'Will set {k} DNP {donotpopulate}')
        c.dnp.value = donotpopulate
        
        count += 1
    
    return count
    
def capsHierLabels(s:Schematic):
    count = 0
    if not hasattr(s, 'hierarchical_label'):
        return 0
    
    for e in s.hierarchical_label:
        e.value = e.value.lower()
        e.effects.font.size.value = [2, 2]
        count += 1
        
    return count

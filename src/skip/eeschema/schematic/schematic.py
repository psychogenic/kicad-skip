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
    
    
    
    def dedicated_collection_type_for(self, entity_type:str):
        dedicatedCollection = {
        
            'symbol': SymbolCollection,
            'wire': WireCollection,
        }
        if entity_type in dedicatedCollection:
            return dedicatedCollection[entity_type]
        return None 
    def dedicated_wrapper_type_for(self, entity_type:str):
        
        dedicatedWrapper = {
            'symbol': Symbol,
            'sheet': SheetWrapper,
            'lib_symbols': LibSymbolsListWrapper, # this single element acts like a list (children)
            'wire': WireWrapper
        }
        if entity_type in dedicatedWrapper:
            return dedicatedWrapper[entity_type]
        
        return None 
    
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

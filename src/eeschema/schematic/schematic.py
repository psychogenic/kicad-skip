'''
Main handle to kicad schematic.

This is the top level object for all the action in this library.  If you


import eeschema
sch = eeschema.Schematic('path/to/file.kicad_sch')


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
  * a container of objects

Dedicated containers are used in some instances.  These can act just like lists

for component in sch.symbol:
    print(f'Setting datasheet and DNP on {component.property.reference.value}')
    component.property.datasheet.value = 'Ho.pdf'
    component.dnp = True

But often also as objects with attributes. For symbols (components) these are the
reference of the component, which is very useful when operating in a console.

Use tab-completion to see them all

sch.symbol.<TAB><TAB>

and use 'em.
sch.symbol.C42.dnp = True


Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from eeschema.sexp.util import loadTree, writeTree
from eeschema.sexp.parser import ParsedValue
from eeschema.schematic.symbol import SymbolContainer, SymbolWrapper
from eeschema.sheet import SheetWrapper
import logging 
log = logging.getLogger(__name__)

class Schematic:
    def __init__(self, filepath:str):
        '''
            c'tor for the schematic object, gateway to everything in the 
            kicad_sch file.
            
            @param filepath: path/to/schematic.kicad_sch
            
            This is the main handle to a schematic sheet.
            
            @note: No checking is done at all.  If the file DNE, it dies.  
            If it's not a kicad schematic... who knows.
        '''
        self.tree = None
        self._symbols_by_name = None
        self._added_attribs = []
        self.read(filepath)
    
    def read(self, filepath:str):
        '''
            Read in a kicad_sch file.
            @param filepath: path/to/schematic.kicad_sch
        '''
        self._filepath = filepath
        self.tree = loadTree(filepath)
        self._symbols_by_name = None
        
        
        if len(self._added_attribs):
            # we've generated attribs, this is a reload/fresh load
            # get rid of old stuff hanging around
            for aname in self._added_attribs:
                delattr(self, aname)
        
        # clear out the list
        self._added_attribs = []
            
        bytype = {}
        for i, level in enumerate(self.tree):
            try:
                pv = ParsedValue(self.tree, level, [i])
                if pv.entity_type not in bytype:
                    bytype[pv.entity_type] = []
                
                bytype[pv.entity_type].append(pv)
            except Exception as e:
                print(f"Problem parsing entry {i}:\n{level}")
                print(e)
        
        self._all = bytype
        dedicatedContainer = {
        
            'symbol': SymbolContainer
        }
        dedicatedWrapper = {
            'symbol': SymbolWrapper,
            'sheet': SheetWrapper
        }
        for k,v in bytype.items():
            
            if k is None:
                continue 
            
            
            self._added_attribs.append(k)
            if k in dedicatedWrapper:
                wrapClass = dedicatedWrapper[k]
                numVals = len(v)
                if numVals:
                    v = list(map(lambda baseobj: wrapClass(baseobj), v))
            
            if k is not None:
                # this can lead to surprises (eg sheet) but makes life simpler in most cases
                if len(v) == 1: 
                    setattr(self, k, v[0]) 
                elif len(v) > 1:
                    if k in dedicatedContainer:
                        setattr(self, k, dedicatedContainer[k](v))
                    else:
                        setattr(self, k, v)
    
    def write(self, fpath:str):
        '''
            Write current schematic tree to file.
            @param fpath: path/to/output.kicad_sch
            
            @note: writes the file you specify no checks or hand-holding 
        '''
        writeTree(fpath, self.tree)
        log.info(f"Wrote tree to {fpath}")
        
    
    def reload(self):
        '''
            reloads originally loaded file
        '''
        log.info(f"Reloading '{self._filepath}'")
        self.read(self._filepath)
        
    def overwrite(self):
        '''
            overwrites originally loaded file
        '''
        log.info(f"Overwriting loaded file '{self._filepath}'")
        self.write(self._filepath)   
         
    
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

'''
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
        self.tree = None
        self._symbols_by_name = None
        self.read(filepath)
    
    def read(self, filepath:str):
        self._filepath = filepath
        self.tree = loadTree(filepath)
        self._symbols_by_name = None
            
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
        writeTree(fpath, self.tree)
        log.info(f"Wrote tree to {fpath}")
        
    
    def reload(self):
        log.info(f"Reloading '{self._filepath}'")
        self.read(self._filepath)
        
    def overwrite(self):
        log.info(f"Overwriting loaded file '{self._filepath}'")
        self.write(self._filepath)   
         
    @property
    def symbols_by_nameDEADBEEF(self):
        if self._symbols_by_name is None:
            if not hasattr(self, 'symbol'):
                return None
            
            self._symbols_by_name = dict()
            for s in self.symbol:
                ref = s.property.reference.value
                if ref in self._symbols_by_name:
                    log.warn(f'You have duplicate "{ref}" in this schematic..?')
                    
                self._symbols_by_name[ref] = s
                
        return self._symbols_by_name
        
    
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

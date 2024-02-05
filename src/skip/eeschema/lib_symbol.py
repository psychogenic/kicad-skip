'''
Created on Feb 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from skip.collection import NamedElementCollection
from skip.sexp.parser import ParsedValue, ParsedValueWrapper
from skip.eeschema.schematic.symbol import SymbolBase
from skip.eeschema.pin import Pin


# property_changed

class LibSymbolsListWrapper(NamedElementCollection):
    '''
        This one is weird... a single element libsymbols acts like a list 
        for its children
    '''
    
    def __init__(self, pv:ParsedValue):
        super().__init__(None, [], None)
        self._pv = pv
        self._libsyms_by_id = dict()
        self._libsyms_attrib_names = []
        for i in range(len(pv.children)):
            c = LibSymbol(pv[i])
            pv.children[i] = c 
            c_name = c.value
            self._libsyms_by_id[c_name] = c # 
            self._libsyms_attrib_names.append(pv[i].toSafeAttributeKey(c_name))
            self.append(c)
            self.elementAdd(c_name, c)
            
    
    def __contains__(self, key):
        return key in self._libsyms_by_id
    
    def __getitem__(self, key:int):
        '''
            syms by id
        '''
        if key in self._libsyms_by_id:
            return self._libsyms_by_id[key]
        
        
        raise AttributeError(f'No {key} here')
    
    def property_changed(self, name:str, to_value:str, from_value:str):
        return # nothing to do

class LibSymbolsListWrapperOLD(ParsedValueWrapper):
    '''
        All lib symbols available.
        
    '''
    
    def __init__(self,v:ParsedValue):
        super().__init__(v)
        self._layer_attrib_names = []
        self._layers_by_id = {}
        self._layers_children_list = []
        for i in range(len(v.children)):
            c = LibSymbol(v[i])
            v.children[i] = c 
            c_name = c.value
            c_clean = v.toSafeAttributeKey(c_name)
            self._layers_by_id[c_name] = c # 
            self._layer_attrib_names.append(c_clean)
            setattr(self, c_clean, c)
    
    
    def __contains__(self, key):
        return key in self._layers_by_id
    
    def __getitem__(self, key:int):
        '''
            layers by id
        '''
        if key in self._layers_by_id:
            return self._layers_by_id[key]
        
        
        raise AttributeError(f'No {key} here')
        
        
    def __len__(self):
        return len(self.children)
    
    def __dir__(self):
        return super().__dir__() + self._layer_attrib_names
    
    
    def __repr__(self):
        return f'<LibSymbols ({len(self)})>'
    
    
class LibSymbolPin(Pin):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        
    @property 
    def name(self):
        return self.wrapped_parsed_value.name
    
    def __repr__(self):
        return f'<Pin {self.number.value} "{self.name.value}">'


class LibSymbolElementWithPins(NamedElementCollection):
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements, lambda lspin: lspin.number.value if lspin.name.value == '~' else lspin.name.value)
        

class LibSymbol(SymbolBase):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        self._pins_cache = None 
        self._symbol_units = []
        
        all_pins = []
        subsyms = pv.symbol
        if not isinstance(pv.symbol, list):
            subsyms = [pv.symbol]
        for es in subsyms:
            espins = []
            if hasattr(es, 'pin'):
                for pn in es.getElementsByEntityType('pin'):
                    pobj = LibSymbolPin(pn)
                    all_pins.append(pobj)
                    espins.append(pobj)
                    
                # replace it
                es.pin = LibSymbolElementWithPins(self, espins)
            self._symbol_units.append(es)
            
        self._all_pins = LibSymbolElementWithPins(self, all_pins)
            
    
    @property 
    def container(self):
        return self.parent_top.lib_symbols
    
    @property 
    def symbol(self):
        return self._symbol_units
        
    @property
    def pin(self):
        return self._all_pins
        
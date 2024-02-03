'''
Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import re
from skip.property import ElementWithPropertiesWrapper
from skip.container import NamedElementContainer
from skip.sexp.parser import ParsedValue, ParsedValueWrapper
from skip.at_location import AtValue
from skip.eeschema.pin import Pin
class SymbolContainer(NamedElementContainer):
    '''
        The symbols of a schematic are all contained in this.
        
        It acts like both a list and an object where each component is an attribute
        
        for component in schem.symbol:
            print(component.property.Reference.value)
            
        # or 
        if len(schem.symbol) > 4:
            print(schem.symbol[4])
        
        It also has each component as an attribute, so you can used named syntax
        
        print(schem.symbol.C12.property.datasheet)
        
        Use <TAB> completion in the console to explore the available.
        schem.symbol.<TAB><TAB> is great
        
        Also some utility methods, below

    '''
    def __init__(self, elements:list):
        super().__init__(elements, lambda s: s.property.Reference.value)
        
        
        
    def reference_startswith(self, prefix:str):
        '''
            Get a list of all the symbols for which the reference starts with prefix.
            
            Easy enough to filter() on this, but
            
              sch.symbol.reference_startswith('C')
              
            will give you a list of all the caps.  
        '''
        return list(filter(lambda s: s.property.Reference.value.startswith(prefix), self))
    
    def reference_matches(self, regex:str):
        '''
            Similar to reference_startswith but with regular expressions.
            
            sch.symbol.reference_matches('R.[1-3]')
            
            would give you all resistors with reference:
              * greater than 10
              * containing a 1,2 or 3 as the second digit
              
            >>> sorted(sch.symbol.reference_matches('R.[1-3]'))
            [<symbol R11>, <symbol R12>, <symbol R13>, <symbol R21>, <symbol R22>, 
            <symbol R23>, <symbol R31>, <symbol R32>, <symbol R33>, <symbol R41>, 
            <symbol R42>, <symbol R43>]
              
        '''
        return list(filter(lambda s: re.match(regex, s.property.Reference.value), self))
    
    def value_startswith(self, prefix:str):
        return list(filter(lambda s: s.property.Value.value.startswith(prefix), self))
    
    def value_matches(self, regex:str):
        return list(filter(lambda s: re.match(regex, s.property.Value.value), self))




class SymbolBase(ElementWithPropertiesWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        
    def __lt__(self, other):
        return self.property.Reference.value < other.property.Reference.value
  
    def __repr__(self):
        v = self.property.Reference.value
        baseRef = v
        if hasattr(self, 'instances'):
            for proj in self.instances.getElementsByEntityType('project'):
                if proj.path.reference.value != baseRef:
                    v += f',{proj.value}:{proj.path.reference.value}'
        #except Exception as e:
        #    raise e
        #    v = self.value 
        
        return f'<{self.entity_type} {v}>' # , {len(self.children)} children {str(self.children)}>'



class Symbol(SymbolBase):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        self._sympins_cont_cache = None 
    @property 
    def allReferences(self):
        return self.getElementsByEntityType('reference')
    
    @property
    def is_power(self):
        return self.lib_id.value.startswith('power:')
    
    
    @property 
    def pin(self):
        if self._sympins_cont_cache is None:
            lib_pins_map = dict()
            for lib_pin in self.lib_symbol.pin:
                lib_pins_map[lib_pin.number.value] = lib_pin 
            
            pseudoPinsList = []
            for sym_pin in self.wrapped_parsed_value.pin:
                pin_num = sym_pin.value 
                
                matchingLibPin = None
                if pin_num in lib_pins_map:
                    matchingLibPin = lib_pins_map[pin_num]
                pseudoPinsList.append(SymbolPin(sym_pin, matchingLibPin))

            self._sympins_cont_cache = SymbolPinContainer(pseudoPinsList, lambda sp: sp.number if sp.name == '~' else sp.name)
            
        return self._sympins_cont_cache
            
    
    @property 
    def attached_wires(self):
        all_wires = []
        for p in self.pin:
            pwires = p.attached_wires
            all_wires.extend(pwires)
        
        return all_wires
                
    
    @property 
    def lib_symbol(self):
        if hasattr(self, 'lib_id') and len(self.lib_id.value):
            if hasattr(self.parent, 'lib_symbols'):
                try:
                    return self.parent.lib_symbols[self.lib_id.value]
                except:
                    pass 
        
        return None 
    
class SymbolPinContainer(NamedElementContainer):
    pass

class SymbolPin(Pin):
    
    def __init__(self, sympin:ParsedValue, lib_pin:ParsedValue):
        super().__init__(sympin)
        
        self._lib_sym_pin = lib_pin
        
    @property 
    def name(self):
        return self._lib_sym_pin.name.value 
    
    @property
    def number(self):
        return self._lib_sym_pin.number.value
    
    @property 
    def location(self):
        par_at = AtValue(self.parent.at.value)
        
        rel_at = AtValue(self._lib_sym_pin.at.value)
        manip_at = AtValue(self._lib_sym_pin.at.value)
        manip_at.rotation = 0  # whatever the pin is set to, it's in the part "0 state"
        
        # this ain't pretty, but its simple
        while manip_at.rotation != par_at.rotation:
            manip_at.rotate90degrees()
            rel_at.rotate90degrees()
        
        return AtValue([    
                    round(par_at.x + rel_at.x, 4),
                    round(par_at.y - rel_at.y, 4), # note the - !!coords in lib editor are flipped kinda
                    rel_at.rotation])
        
    @property 
    def attached_wires(self):
        loc = self.location 
        if not hasattr(self.parent.parent, 'wire'):
            return []
        
        return self.parent.parent.wire.all_at(loc.x, loc.y)
    
    @property 
    def attached_labels(self):
        all_labels = []
        for w in self.attached_wires:
            for lbl in w.list_labels(recursive_crawl=True):
                if lbl not in all_labels:
                    all_labels.append(lbl)
                    
        return all_labels
    
    @property 
    def attached_global_labels(self):
        all_labels = []
        for w in self.attached_wires:
            for lbl in w.list_global_labels(recursive_crawl=True):
                if lbl not in all_labels:
                    all_labels.append(lbl)
                    
        return all_labels
        
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return f'<SymbolPin {self.number} "{self.name}">'
        

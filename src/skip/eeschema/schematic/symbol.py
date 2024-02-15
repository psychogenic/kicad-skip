'''
Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import re
import copy
from skip.property import ElementWithPropertiesWrapper
from skip.collection import NamedElementCollection
from skip.sexp.parser import ParsedValue
from skip.at_location import AtValue
from skip.eeschema.pin import Pin


class SymbolCollection(NamedElementCollection):
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
    UnitToName = ['N/A', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements, 
                         lambda s: s.property.Reference.value if s.unit.value == 1 else f'{s.property.Reference.value}_{self.UnitToName[s.unit.value]}')
        
        self._multi_unit_elements = dict()
        for el in elements:
            if el.unit.value > 1:
                self._multi_unit_elements[el.property.Reference.value] = True
                
        for multis in self._multi_unit_elements.keys():
            self.elementRename(multis, f'{multis}_{self.UnitToName[1]}')
            
    
    @classmethod 
    def name_for(cls, element):
        return element.property.Reference.value 
    
    
    @classmethod 
    def set_name_for(cls, to_name:str, element):
        element.property.Reference.value = to_name
        
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

    def multiple_units_for_reference(self, reference:str):
        return reference in self._multi_unit_elements
    
    
    def property_changed(self, name:str, to_value:str, from_value:str):
        if name != 'Reference':
            return 
        
        self.elementRename(from_value, to_value)


class SymbolBase(ElementWithPropertiesWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        
        
    
    @property 
    def container(self):
        return NotImplementedError('override container property!')
    
    
    def __lt__(self, other):
        return self.property.Reference.value < other.property.Reference.value
  
    def __repr__(self):
        v = self.property.Reference.value
        baseRef = v
        if 'instances' in self:
            for proj in self.instances.getElementsByEntityType('project'):
                if proj.path.reference.value != baseRef:
                    v += f',{proj.value}:{proj.path.reference.value}'
        #except Exception as e:
        #    raise e
        #    v = self.value 
        
        return f'<{self.entity_type} {v}>' # , {len(self.children)} children {str(self.children)}>'



class Symbol(SymbolBase):
    '''
        Symbol: the components in a schematic
        
        There are many plain attributes, such as 
            in_bom
            dnp
            on_board
        etc.
        
        Properties are available through the collection as
         * a list
             for prop in sym.property:
                 # do stuff
         * attributes as sym.property.NAME, e.g.
             sym.property.Reference 
             etc.
        
        Pins are available through the pin attribute, 
        another collection, so as a list
        
            >>> for p in sym.pin:
            ...     p
            ... 
            <SymbolPin 1 "VIN">
            <SymbolPin 2 "GND">
            <SymbolPin 3 "EN">
            <SymbolPin 4 "NC">
            <SymbolPin 5 "VOUT">
            
        or named
        sym.pin.EN
        
        Utility methods are around to see what's actually 
        attached to the symbol.
        
        
    '''
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        self._sympins_cont_cache = None 
        
    @property 
    def Reference(self):
        return self.property.Reference 
    
    @property
    def Value(self):
        return self.property.Value
    @property 
    def allReferences(self):
        return self.getElementsByEntityType('reference')
    
    def setAllReferences(self, toValue:str):
        '''
            Set all references, both the 
            property.Reference
            and the annoying instances.project[*].path.reference values 
        '''
        self.property.Reference.value = toValue
        if hasattr(self, 'instances'):
            for ref in self.instances.getElementsByEntityType('reference'):
                ref.value = toValue
                
    @property
    def is_power(self):
        '''
            whether this is from the power library 
            (e.g. a GND symbol etc)
        '''
        return self.lib_id.value.startswith('power:')
    
    
    @property 
    def pin(self):
        '''
            The collection of pins.
            Pins are available through the pin attribute, 
            another collection, so as a list
            
                >>> for p in sym.pin:
                ...     p
                ... 
                <SymbolPin 1 "VIN">
                <SymbolPin 2 "GND">
                <SymbolPin 3 "EN">
                <SymbolPin 4 "NC">
                <SymbolPin 5 "VOUT">
                
            or named
            sym.pin.EN
            
            use the REPL and tab completion to have a look.
        '''
            
        if self._sympins_cont_cache is not None:
            return self._sympins_cont_cache
        lib_pins_map = dict()
        
        if self.parent.symbol.multiple_units_for_reference(self.property.Reference.value):
            lib_sym_pins = self.lib_symbol.symbol[self.unit.value - 1].pin
        else:
            lib_sym_pins = self.lib_symbol.pin
        
        for lib_pin in lib_sym_pins:
            lib_pins_map[lib_pin.number.value] = lib_pin 
        
        pseudoPinsList = []
        for sym_pin in self.wrapped_parsed_value.pin:
            pin_num = sym_pin.value 
            
            matchingLibPin = None
            if pin_num in lib_pins_map:
                matchingLibPin = lib_pins_map[pin_num]
                pseudoPinsList.append(SymbolPin(sym_pin, matchingLibPin))

        self._sympins_cont_cache = SymbolPinCollection(self, pseudoPinsList, lambda sp: sp.number if sp.name == '~' else sp.name)
            
        return self._sympins_cont_cache
            
    
    @property 
    def attached_wires(self):
        '''
            Wires directly attached to the pins of this symbol
        '''
        all_wires = []
        for p in self.pin:
            pwires = p.attached_wires
            #print(f"WIRES FROM {p}:\n{pwires}")
            all_wires.extend(pwires)
        
        return all_wires
    
    
    
    @property 
    def attached_labels(self):
        '''
            Labels attached to the wires that are attached to this symbol
        '''
        all_labels = []
        for p in self.pin:
            for lbl in p.attached_labels:
                if lbl not in all_labels:
                    all_labels.append(lbl)
        
        return all_labels
    
    @property 
    def attached_global_labels(self):
        '''
            Global labels attached to the wires that are attached to this symbol
        
        '''
        all_labels = []
        for p in self.pin:
            for lbl in p.attached_global_labels:
                if lbl not in all_labels:
                    all_labels.append(lbl)
        
        return all_labels
    
    
    @property 
    def attached_symbols(self):
        '''
            Symbols attached to the wires attached to the pins of the symbol -- oof
        '''
        all_symbols = []
        for w in self.attached_wires:
            for sym in w.list_connected_symbols(True):
                if sym != self and sym not in all_symbols:
                    all_symbols.append(sym)
                    
        return all_symbols
        
        
    @property 
    def attached_all(self):
        all_attached = self.attached_symbols
        all_attached.extend(self.attached_global_labels)
        all_attached.extend(self.attached_labels)
        return all_attached
    
                
    
    @property 
    def lib_symbol(self):
        '''
            The library symbol this symbol is based on.  
            The id is in the lib_id attribute.  This is an 
            object instance.
        '''
        if hasattr(self, 'lib_id') and len(self.lib_id.value):
            if hasattr(self.parent, 'lib_symbols'):
                
                #if self.unit.value > 1:
                #    return self.parent.lib_symbols[self.lib_id.value].symbol[self.unit.value - 1]
                
                try:
                    return self.parent.lib_symbols[self.lib_id.value]
                except:
                    pass 
        
        return None 
    
    @property 
    def container(self):
        return self.parent.symbol
    
    def __repr__(self):
        if self.unit is not None and self.unit.value != 1:
            return f'<symbol {self.property.Reference.value} (unit {SymbolCollection.UnitToName[self.unit.value]})>'
        return super().__repr__()
    
class SymbolPinCollection(NamedElementCollection):
    pass

class SymbolPin(Pin):
    '''
        Symbol pin.
        
        Have a name and number and a location, which is 
        calculated based on the state of the parent symbol and 
        the definitions in the library symbol.
        
    '''
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
        rel_at_raw = copy.deepcopy(self._lib_sym_pin.at.value)
        if hasattr(self.parent, 'mirror'):
            mval = self.parent.mirror.value 
            
            if hasattr(mval, 'value'):
                mval = mval.value()
            rot = rel_at_raw[2] 
            if mval == 'y': # around y
                rel_at_raw[0] = -1 * rel_at_raw[0]
                if rot % 180 == 0:
                    rel_at_raw[2] = (rot + 180) % 360
            elif mval == 'x':
                rel_at_raw[1] = -1 * rel_at_raw[1]
                if rot % 90 == 0:
                    rel_at_raw[2] = (rot + 180) % 360
                    
                
        rel_at = AtValue(rel_at_raw)
        manip_at = AtValue(rel_at_raw)
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
        '''
            Wires attached to this pin
        
        '''
        loc = self.location 
        if not hasattr(self.parent.parent, 'wire'):
            print("NO GLOB WIRE??")
            return []
        
        return self.parent.parent.wire.all_at(loc.x, loc.y)
    
    @property 
    def attached_labels(self):
        '''
            Labels connected to wires attached to this pin
        
        '''
        all_labels = set()
        for w in self.attached_wires:
            for lbl in w.list_labels(recursive_crawl=True):
                all_labels.add(lbl)
                    
        return list(all_labels)
    
    @property 
    def attached_global_labels(self):
        '''
            Global labels connected to wires attached to this pin
        
        '''
        all_labels = set()
        for w in self.attached_wires:
            for lbl in w.list_global_labels(recursive_crawl=True):
                all_labels.add(lbl)
                    
        return list(all_labels)
    
    
    @property 
    def attached_symbols(self):
        '''
            Symbols connected to wires attached to this pin
        
        '''
        all_syms = []
        for w in self.attached_wires:
            all_syms.extend(w.list_connected_symbols(recursive_crawl=True))
            
        return all_syms
    
    @property 
    def attached_all(self):
        all_attached = self.attached_symbols
        all_attached.extend(self.attached_global_labels)
        all_attached.extend(self.attached_labels)
        return all_attached
    
        
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return f'<SymbolPin {self.number} "{self.name}">'
        

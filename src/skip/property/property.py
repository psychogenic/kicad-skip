'''
Created on Jan 30, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
from skip.collection import NamedElementCollection, ElementCollection
from skip.sexp.parser import ParsedValueWrapper, ParsedValue, ArbitraryNamedParsedValueWrapper

class PropertyCollection(NamedElementCollection):
    '''
        Properties, like those of components (Reference, Datasheet, MPN, etc)
        are special in that you can name them yourself, so they are 
        different than most other entries in the schematic.
        This collection replaced the simple list to allow of both indexed
            sym.property[0], len(obj.property)
        and named attributes
            sym.property.Reference 
        so 
            sym.property.<TAB><TAB> will show you all that's available.
        
        Some properties are always defined (e.g. datasheet) but others you may have 
        added yourself.  To check for presence, you can just use "in"
        
        if 'MPN' in sym.property:
            print(sym.property.MPN.value)
        
        
    '''
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements, 
                         lambda p: re.sub(r'[^\w\d_]', '_', p.children[0]))
        
    
    def property_changed(self, name:str, to_value:str, from_value:str):
        self.parent.container.property_changed(name, to_value, from_value)

class PropertyString(ArbitraryNamedParsedValueWrapper):
    
    '''
        Property strings have pseudo-arbitrary names, on top of the 
        value and children of other expression elements.
        
        Thus you can set the value:
        component.property.Reference.value = 'C10'
        
        But you could also change the things name, say
        
        component.property.MPN.name
        'MPN'
        component.property.MPN.name = 'Manufacturer'
        
        # now the property contains a cleansed version of the name, attribute:
        
        component.property.Manufacturer.value
        
        @note: I would not recommend changing any of the standard/required properties, like Reference and Description
    
    '''
    
    def __init__(self, pv:ParsedValue, propertyCollection:NamedElementCollection=None):
        super().__init__(pv)
        self._collection = propertyCollection
        
    def clone(self):
        cloned_el = self.wrapped_parsed_value.clone()
        
        # don't want to overwrite the existing, so must 
        # change name, but to do this safely collection must
        # not be set yet
        prop = type(self)(cloned_el)
        prop.name = f'{prop.name}_'
        # now set the collection
        prop._collection = self._collection
        # and addit
        self._collection.append(prop)
        return prop
    
    def __repr__(self):
        return f"<PropertyString {self.name} = '{self.value}'>"
        
    def setValue(self, x):
        old_value = self.getValue()
        super().setValue(x)
        self._collection.property_changed(self.name, self.getValue(), old_value)
        
    
    def setParentCollection(self, propertyCollection:NamedElementCollection):
        self._collection = propertyCollection
        
    def updateParentCollection(self, oldName:str, newName:str):
        if self._collection is None:
            return 
        self._collection.elementRemove(oldName)
        self._collection.elementAdd(newName, self)
        
class ElementWithPropertiesWrapper(ParsedValueWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        props = []
        if hasattr(pv, 'property'):
            for p in pv.property:
                props.append(PropertyString(p))
        
        pv.property = PropertyCollection(self, props)
        
        # ugh, this ain't pretty refactor later
        # only used to allow for changing the things name
        for p in props:
            p.setParentCollection(pv.property)
            
            
        
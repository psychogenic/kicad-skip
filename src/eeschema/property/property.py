'''
Created on Jan 30, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
from eeschema.schematic.container import NamedElementContainer
from eeschema.sexp.parser import ParsedValueWrapper, ParsedValue, ArbitraryNamedParsedValueWrapper

class PropertyContainer(NamedElementContainer):
    '''
        Properties, like those of components (Reference, Datasheet, MPN, etc)
        are special in that you can name them yourself, so they are 
        different than most other entries in the schematic.
        This container replaced the simple list to allow of both indexed
            obj.property[0], len(obj.property)
        and named attributes
            obj.property.reference 
        
    '''
    def __init__(self, elements:list):
        super().__init__(elements, 
                         lambda p: re.sub(r'[^\w\d_]', '_', p.children[0].lower()))

class PropertyString(ArbitraryNamedParsedValueWrapper):
    def __repr__(self):
        return f"<PropertyString {self.name} = '{self.value}'>"
        
    
        
class ElementWithPropertiesWrapper(ParsedValueWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        props = []
        for p in pv.property:
            props.append(PropertyString(p))
            
        pv.property = PropertyContainer(props)
        
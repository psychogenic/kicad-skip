'''
Created on Feb 15, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
import copy
from skip.property import ElementWithPropertiesWrapper
from skip.collection import NamedElementCollection
from skip.sexp.parser import ParsedValue, ParsedValueWrapper, ArbitraryNamedParsedValueWrapper
from skip.pcbnew.layer import LayerPropertyHandler

import logging 
log = logging.getLogger(__name__)
class FootprintCollection(NamedElementCollection):
    '''

    '''
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements, 
                         lambda s: s.Reference.value)
    
    @classmethod 
    def name_for(cls, element):
        return element.Reference.value 
    
    
    @classmethod 
    def set_name_for(cls, to_name:str, element):
        element.Reference.value = to_name
        
    def reference_startswith(self, prefix:str):
        '''
        '''
        return list(filter(lambda s: s.Reference.value.startswith(prefix), self))
    
    def reference_matches(self, regex:str):
        '''
        '''
        return list(filter(lambda s: re.match(regex, s.Reference.value), self))
    
    def value_startswith(self, prefix:str):
        return list(filter(lambda s: s.Value.value.startswith(prefix), self))
    
    def value_matches(self, regex:str):
        return list(filter(lambda s: re.match(regex, s.Value.value), self))

    def property_changed(self, name:str, to_value:str, from_value:str):
        if name != 'reference':
            return 
        
        self.elementRename(from_value, to_value)


class FootprintText(ArbitraryNamedParsedValueWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        
        
    def __repr__(self):
        return f"<FootprintText {self.name} = '{self.value}'>"
    

class FootprintWrapper(ElementWithPropertiesWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        
        footprint_text = []
        for fptxt in pv.fp_text:
            footprint_text.append(FootprintText(fptxt))
        
        self.fp_text = NamedElementCollection(self, footprint_text, lambda fptxt: fptxt.name)
        
        self._layer_handler = LayerPropertyHandler(pv.layer, self.parent)

        
        
    @property 
    def Reference(self):
        if 'reference' in self.fp_text:
            return self.fp_text.reference 
        
        return None
        
    @property 
    def Value(self):
        if 'value' in self.fp_text:
            return self.fp_text.value
        
        
    @property
    def layer(self):
        return self._layer_handler.get()
    
    @layer.setter 
    def layer(self, setTo):
        return self._layer_handler.set(setTo)
    
    
    
    def __repr__(self):
        if self.Reference is not None:
            return f"<Footprint {self.Reference.value}>"
        
        return '<Footprint [No ref]>'
    
    
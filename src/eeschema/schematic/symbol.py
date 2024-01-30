'''
Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import re
from eeschema.property import ElementWithPropertiesWrapper
from eeschema.schematic.container import NamedElementContainer
from eeschema.sexp.parser import ParsedValueWrapper, ParsedValue
class SymbolContainer(NamedElementContainer):
    def __init__(self, elements:list):
        super().__init__(elements, lambda s: s.property.reference.value)
        
    def reference_startswith(self, prefix:str):
        return list(filter(lambda s: s.property.reference.value.startswith(prefix), self))
    
    def reference_matches(self, regex:str):
        return list(filter(lambda s: re.match(regex, s.property.reference.value), self))
            


class DEADBEEF(ParsedValueWrapper):
    def __init__(self, sourceTree, name, itm):
        super().__init__(sourceTree)
        self._itm = itm
        self.name = name 
        coords = []
        for i in itm._base_coords:
            coords.append(i)                        
        coords.append(2)
        self._write_coords = coords
        
        for child in itm.children:
            if isinstance(child, ParsedValue):
                setattr(self, child.entity_type, child)
    
    @property 
    def raw(self):
        return self._itm.raw
    
    
    @property 
    def raw_parent(self):
        return self._itm.raw_parent
    
    @property 
    def value(self): 
        return self._itm.children[1]
    
    @value.setter
    def value(self, x):
        self._itm.children[1] = x
        self._setOnTree(self._write_coords, x)
        
    def __getattr__(self, name:str):
        if hasattr(self._itm, name):
            return getattr(self._itm, name)
        
    
        
    def __repr__(self):
        return f"<PropertyString {self.name} = '{self.value}'>"
        

class SymbolWrapper(ElementWithPropertiesWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        
    @property 
    def allReferences(self):
        return self.getElementsByEntityType('reference')
    
    
    def __repr__(self):
        v = self.property.reference.value
        baseRef = v
        if hasattr(self, 'instances'):
            for proj in self.instances.getElementsByEntityType('project'):
                if proj.path.reference.value != baseRef:
                    v += f',{proj.value}:{proj.path.reference.value}'
        #except Exception as e:
        #    raise e
        #    v = self.value 
        
        return f'<{self.entity_type} {v}>' # , {len(self.children)} children {str(self.children)}>'

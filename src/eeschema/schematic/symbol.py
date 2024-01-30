'''
Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import re
from eeschema.property.property import ElementWithPropertiesWrapper
from eeschema.schematic.container import NamedElementContainer
from eeschema.sexp.parser import ParsedValue
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
    

class Symbol(ElementWithPropertiesWrapper):
    def __init__(self, pv:ParsedValue):
        super().__init__(pv)
        
    @property 
    def allReferences(self):
        return self.getElementsByEntityType('reference')
    
    @property
    def is_power(self):
        return self.lib_id.value.startswith('power:')
    
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

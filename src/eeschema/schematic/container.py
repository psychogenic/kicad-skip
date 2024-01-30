'''
Base classes for custom containers

Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
class ElementContainer:
    '''
        A base class for element containers.
        
        Acts like a list
        
        for element in container:
            # do something
            
        if len(container) > 6:
            container[6].whatever
        
    '''
    def __init__(self, elements:list):
        self._elements = elements 
        
    def __getitem__(self, index:int):
        return self._elements[index]
        
    def __len__(self):
        return len(self._elements)
    
    def __repr__(self):
        return f'<Container {self._elements}>'

    
    def __str__(self):
        els = map(lambda e: str(e), self._elements)
        return '\n'.join(els)

class NamedElementContainer(ElementContainer):
    '''
        Named elements are those without a fixed name/key/type, e.g. the 
        properties of a symbol.
        
        This container allows for list-like operation 
            for element in container:
                # do something
                
            if len(container) > 6:
                container[6].whatever
        
        but also for named attributes
            container.something_within 
        so 
            container.<TAB><TAB> will show you all that's available.
        
        @see: property.PropertyContainer for real examples.
        
    '''
    def __init__(self, elements:list, namefetcher):
        super().__init__(elements)
        self._named = dict()
        for el in elements:
            name = namefetcher(el)
            
            name = re.sub(r'[^\w\d_]', '_', name)
            self._named[name] = el
            
            
    def elementRemove(self, elKey:str):
        del self._named[elKey]
        
    def elementAdd(self, elKey:str, element):
        self._named[elKey] = element 
        
    def __contains__(self, key:str):
        return key in self._named
    
    def __getattr__(self, key:str):
        if key in self._named:
            return self._named[key]
        # named element are dynamic, so we 
        # can't know if the key is present -- return None if not
        #raise AttributeError(f"Unknown element {key}")
        return None
        
    def __dir__(self):
        return self._named.keys()
    
        
    
    

        

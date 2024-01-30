'''
Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
class ElementContainer:
    
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
    
    def __init__(self, elements:list, namefetcher):
        super().__init__(elements)
        self._named = dict()
        for el in elements:
            name = namefetcher(el)
            
            name = re.sub(r'[^\w\d_]', '_', name)
            self._named[name] = el
            
    def __getattr__(self, key:str):
        if key in self._named:
            return self._named[key]
        
        raise AttributeError(f"Unknown element {key}")
        
    def __dir__(self):
        return self._named.keys()
    
        
    
    

        

'''
Base classes for custom containers

Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
import math 
class ElementContainer:
    '''
        A base class for element containers.
        
        Mostly just acts like a list
        
            for element in container:
                # do something
                
            if len(container) > 6:
                container[6].whatever
        
        Also has utility methods to find elements within that
        are located within a certain zone or within reach of 
        another element.  See within_circle() and within_reach_of()
        
    '''
    def __init__(self, elements:list):
        self._elements = elements 
        
    def _coordinates_for(self, el):
        coords = None
        if hasattr(el, 'at'):
            coords = el.at.value 
        elif hasattr(el, 'location'):
            coords = el.location.value 
        return coords
    
    def _distance_between(self, coords1:list, coords2:list):
            dx = coords1[0] - coords2[0]
            dy = coords1[1] - coords2[1]
            return math.sqrt( (dx*dx)+(dy*dy))
    
    def within_reach_of(self, element, distance:float):
        '''    
            Find all elements of this container that are within 
            reach of passed element.
            
            @param element: element in question, must have .at or .location
            
            @param distance: maximal distance, in coord units  
            
            @note: only works for elements that have a
            suitable 'at' or 'location' attribute
        
        '''
        coords = self._coordinates_for(element)
        return list(filter(lambda e: e!=element, self.within_circle(coords[0], coords[1], distance)))
            
        
    def within_circle(self, xcoord:float, ycoord:float, radius:float):
        '''    
            Find all elements of this container that are within the 
            circle of radius radius, centered on xcoord, ycoord.
            
            @note: only works for elements that have a
            suitable 'at' or 'location' attribute
        
        '''
        retvals = []
        if not len(self._elements):
            return retvals
        
        
        target_coords = [xcoord, ycoord]
        for el in self:
            coords = self._coordinates_for(el)
            if coords is None:
                continue
            
            if self._distance_between(target_coords, coords) <= radius:
                retvals.append(el)
                
        return retvals
            
        
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
    NameCleanerRegex = re.compile(r'[^\w\d_]')
    def __init__(self, elements:list, namefetcher):
        super().__init__(elements)
        self._named = dict()
        for el in elements:
            name = namefetcher(el)
            
            name = self.NameCleanerRegex.sub('_', name)
            self._named[name] = el
            
    
    def _cleanse_key(self, key:str):
        return  self.NameCleanerRegex.sub('_', key)
    
    
    def elementRemove(self, elKey:str):
        del self._named[elKey]
        
    def elementAdd(self, elKey:str, element):
        self._named[self._cleanse_key(elKey)] = element 
        
    def __contains__(self, key:str):
        return key in self._named
    
    def __getattr__(self, key:str):
        if key in self._named:
            return self._named[key]
        # named element are dynamic, so we 
        # can't know if the key is present -- return None if not
        #raise AttributeError(f"Unknown element {key}")
        return None
        
    def __getitem__(self, indexOrKey):
        if indexOrKey in self._named:
            return self._named[indexOrKey]
        
        return super().__getitem__(indexOrKey)
    
    
    def __dir__(self):
        return self._named.keys()
    
        
    
    

        

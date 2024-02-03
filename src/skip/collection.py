'''
Base classes for custom collections

Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
import math 
import logging 

log = logging.getLogger(__name__)
class ElementCollection:
    '''
        A base class for element collections.
        
        Mostly just acts like a list
        
            for element in collection:
                # do something
                
            if len(collection) > 6:
                collection[6].whatever
        
        Also has utility methods to find elements within that
        are located within a certain zone or within reach of 
        another element.  See within_circle() and within_reach_of()
        
    '''
    def __init__(self, elements:list):
        self._elements = elements 
        
        
    def append(self, element):
        self._elements.append(element)
        
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
            Find all elements of this collection that are within 
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
            Find all elements of this collection that are within the 
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
                if el not in retvals:
                    retvals.append(el)
                
        return retvals
            
        
    def __getitem__(self, index:int):
        return self._elements[index]
        
    def __len__(self):
        return len(self._elements)
    
    def __repr__(self):
        return f'<Collection {self._elements}>'

    
    def __str__(self):
        els = map(lambda e: str(e), self._elements)
        return '\n'.join(els)

class NamedElementCollection(ElementCollection):
    '''
        Named elements are those without a fixed name/key/type, e.g. the 
        properties of a symbol.
        
        This collection allows for list-like operation 
            for element in collection:
                # do something
                
            if len(collection) > 6:
                collection[6].whatever
        
        but also for named attributes
            collection.something_within 
        so 
            collection.<TAB><TAB> will show you all that's available.
        
        @see: property.PropertyCollection for real examples.
        
    '''
    NamePrefixEliminatorRegex = re.compile(r'^[^\w\d]+')
    NameStartsWithDigitRegex = re.compile(r'^\d')
    NameCleanerRegex = re.compile(r'[^\w\d_]+')
    NameMetaEliminatorRegex = re.compile(r'[}{)(\]\[]')
    def __init__(self, elements:list, namefetcher):
        super().__init__(elements)
        self._named = dict()
        for el in elements:
            name = namefetcher(el)
            name = self._cleanse_key(name)
            self._named[name] = el
    
    def _cleanse_key(self, key:str):
        if key is None or not len(key):
            log.warn(f"Passed key {key} -- can't parsy")
            return '_deadbeef'
        
        key = key.replace('~', 'n')
        key = self.NamePrefixEliminatorRegex.sub('', key)
        key = self.NameMetaEliminatorRegex.sub('', key)
        if self.NameStartsWithDigitRegex.match(key):
            key = f'n{key}'
        
        return self.NameCleanerRegex.sub('_', key)
    
    
    def elementRemove(self, elKey:str):
        del self._named[elKey]
        
    def elementAdd(self, elKey:str, element):
        self._named[self._cleanse_key(elKey)] = element 
        
    def elementRename(self, origKey:str, newKey:str):
        cleaned = self._cleanse_key(origKey)
        if cleaned in self._named:
            v = self._named[cleaned]
            del self._named[cleaned]
            self._named[self._cleanse_key(newKey)] = v 
            
        
    def __contains__(self, key:str):
        if key in self._named:
            return True
        log.debug(f'No {key} found here')
        log.debug(f'Available {list(self._named.keys())}')
        return False
    
    def __getattr__(self, key:str):
        if key in self._named:
            return self._named[key]
        if hasattr(key, 'value'):
            # a concession to anyone naturally passing some 
            # parsedValue object to 
            kv = key.value
            if kv in self._named:
                return self._named[kv]
        # named element are dynamic, so we 
        # can't know if the key is present -- return None if not
        #
        log.debug(f'{key} not found... Available {list(self._named.keys())}')
        # return None
        raise AttributeError(f"Unknown element {key}")
        
    def __getitem__(self, indexOrKey):
        if indexOrKey in self._named:
            return self._named[indexOrKey]
        
        return super().__getitem__(indexOrKey)
    
    
    def __dir__(self):
        return self._named.keys()
    
        
    
    

        

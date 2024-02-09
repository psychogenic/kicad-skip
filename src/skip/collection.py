'''
Base classes for custom collections

Created on Jan 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import re
import math 
import uuid
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
    def __init__(self, parent, elements:list):
        self._parent = parent
        self._elements = elements 
        
    @property 
    def parent(self):
        return self._parent 
    
    def append(self, element):
        self._elements.append(element)
    
    def _new_instance(self):
        raise NotImplementedError('Unimplemented')
    
    
    def new(self):
        '''
            Create a fresh element in this collection, base on a template.
        '''
        newObj = self._new_instance()
        if newObj is None:
            log.error('Could not create a new instance')
            return
        for a_uuid in newObj.getElementsByEntityType('uuid'):
            a_uuid.value = str(uuid.uuid4())
            
        self.append(newObj)
        return newObj
        
    def _coordinates_for(self, el):
        coords = None
        if hasattr(el, 'at') and el.at is not None:
            coords = el.at.value 
        elif hasattr(el, 'location') and el.location is not None:
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
            
    def within_rectangle(self, x1coord:float, y1coord:float, x2coord:float, y2coord:float):
        '''
            Find all elements of this collection that are within the 
            rectangle bounded by (x1,y1) - (x2,y2)
        '''
        retvals = []
        if not len(self._elements):
            return retvals
        
        xrange = [x1coord, x2coord] if x1coord < x2coord else [x2coord, x1coord]
        yrange = [y1coord, y2coord] if y1coord < y2coord else [y2coord, y1coord]
    
        for el in self:
            coords = self._coordinates_for(el)
            if coords is None:
                continue
            
            if coords[0] >= xrange[0] and coords[0] <= xrange[1]:
                if coords[1] >= yrange[0] and coords[1] <= yrange[1]:
                    retvals.append(el)
                
        return retvals
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
            
    def between_elements(self, positionedElement1, positionedElement2):
        '''
            return a list of all elements, between these two, i.e. located 
            in the rectangle comprised by each of their locations.
            
            @param positionedElement1: some parsed value with an 'at' or 'location' 
            @param positionedElement2: some parsed value with an 'at' or 'location' 
        '''
        coords1 = self._coordinates_for(positionedElement1)
        coords2 = self._coordinates_for(positionedElement2)
        if coords1 is None or coords2 is None:
            return []
        return self.within_rectangle(coords1[0], coords1[1], coords2[0], coords2[1])
        
        
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
    def __init__(self, parent, elements:list, namefetcher):
        super().__init__(parent, elements)
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
    
    @classmethod 
    def name_for(cls, element):
        return None
    
    
    @classmethod 
    def set_name_for(cls, to_name:str, element):
        return None
    
    def append(self, element):
        super().append(element)
        name_for = self.name_for(element)
        if name_for is not None and len(name_for):
            if name_for in self._named:
                name_for = f'{name_for}_'
                self.set_name_for(name_for, element)
            self.elementAdd(name_for, element)
            
            
    def _new_instance(self, identifier:str):
        raise NotImplementedError('Unimplemented')
    def new(self, identifier:str):
        '''
            Create a fresh element in this collection, base on a template.
        '''
        newObj = self._new_instance(identifier)
        if newObj is None:
            log.error(f'Could not create a new instance named "{identifier}"')
            return 
        for a_uuid in newObj.getElementsByEntityType('uuid'):
            a_uuid.value = str(uuid.uuid4())
        self.append(newObj)
        
        return newObj
            
    def elementRemove(self, elKey:str):
        if elKey in self._named:
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
    
        
    
    

        

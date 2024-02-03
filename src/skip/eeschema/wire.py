'''
Created on Feb 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from skip.container import ElementContainer
from skip.sexp.parser import ParsedValue, ParsedValueWrapper
# from skip.at_location import AtValue

class WireWrapper(ParsedValueWrapper):
    def __init__(self,v:ParsedValue):
        super().__init__(v)
        
    def translation(self, by_x:float, by_y:float):
        for p in self.points:
            p.value = [round(p.value[0] + by_x, 6), round(p.value[1] + by_y, 6)]
            
    
    @property 
    def points(self):
        return self.pts.xy
    
    @property 
    def start(self):
        return self.pts.xy[0]
    
    @property 
    def end(self):
        return self.pts.xy[1]
    
    def __repr__(self):
        return self.wrapped_parsed_value.__repr__()
        

class WireContainer(ElementContainer):
    def __init__(self, elements:list):
        super().__init__(elements)
        
    def all_at(self, x:float, y:float):
        ret_val = []
        
        for w in self:
            for p in w.points:
                if p.value[0] == x and p.value[1] == y:
                    ret_val.append(w)
        
        return ret_val
    
    
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
            append = False
            for p in el.points:
                if self._distance_between(target_coords, p.value) <= radius:
                    append = True
                    
            if append:
                retvals.append(el)
            
        return retvals
        
    def __repr__(self):
        return f'<WireContainer ({len(self)} wires)>'
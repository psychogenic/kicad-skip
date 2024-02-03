'''
Created on Feb 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import copy
from skip.sexp.parser import ParsedValueWrapper, ParsedValue

class AtValue:
    def __init__(self, vallist:list):
        self._value = copy.deepcopy(vallist)
    @property 
    def value(self):
        return self._value
    
    @value.setter 
    def value(self, setTo:list):
        self._value = setTo
        
        
    @property 
    def x(self):
        return self._value[0]

    @property
    def y(self):
        return self._value[1]
    
    @property 
    def rotation(self):
        return self._value[2]
    
    @rotation.setter
    def rotation(self, setTo:int):
        self._value[2] = setTo
    
    def rotate90degrees(self):
        
        rotation = (self.rotation + 90) % 360
        
        new_x = self.y 
        new_y = -1 * self.x 
        
        self._value = [new_x, new_y, rotation]
        
    def rotateTo(self, degrees:int):
        
        if degrees > 360 or (degrees % 90) != 0:
            raise ValueError('Only 0, 90, 180, 270 allowed')
        
        steps = 0
        while self.rotation != degrees:
            steps += 1
            self.rotate90degrees()
            
        return steps
        
    def __repr__(self):
        return f'<AtValue ({self.x}, {self.y}, {self.rotation})>'

class At(ParsedValueWrapper):
    
    def __init__(self, atpv:ParsedValue):
        super().__init__(atpv)
        self._atval = AtValue(atpv.value)
        
        
    def rotate90degrees(self):
        self._atval.rotate90degrees()
        self.value = self._atval.value
    

    
    
    
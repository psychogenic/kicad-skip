'''
Created on Feb 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from skip.sexp.parser import ParsedValue, ParsedValueWrapper
from skip.at_location import AtValue 
class Pin(ParsedValueWrapper):
    
    def __init__(self, p:ParsedValue):
        super().__init__(p)
        
    @property 
    def name(self):
        return self.wrapped_parsed_value.value[0] 
    
    @property 
    def location(self):
        return AtValue(self.at.value)

    def __repr__(self):
        return f'<Pin "{self.name}">'
        
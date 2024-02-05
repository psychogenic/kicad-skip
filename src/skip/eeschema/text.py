'''
Created on Feb 5, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from skip.collection import ElementCollection
from skip.sexp.parser import ParsedValue, ParsedValueWrapper
from skip.element_template import ElementTemplate

class TextWrapper(ParsedValueWrapper):
    def __repr__(self):
        valstr = self.value 
        
        if valstr is not None:
            if len(valstr) > 9:
                valstr = f'{valstr[:9]}...'
            return f'<{self.entity_type} {valstr}>'
        
        return f'<{self.entity_type}>'


class TextCollection(ElementCollection):
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements)
        
    def _new_instance(self):
        newObj = TextWrapper(self.parent.new_from_list(ElementTemplate['text']))
        return newObj
    
    
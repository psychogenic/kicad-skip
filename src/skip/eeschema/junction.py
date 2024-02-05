'''
Created on Feb 5, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
'''
Created on Feb 5, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from skip.collection import ElementCollection
from skip.sexp.parser import ParsedValueWrapper
from skip.element_template import ElementTemplate

class JunctionWrapper(ParsedValueWrapper):
    def __repr__(self):
        return f'<Junction {self.at.value}>'


class JunctionCollection(ElementCollection):
    def __init__(self, parent, elements:list):
        super().__init__(parent, elements)
        
    def _new_instance(self):
        newObj = JunctionWrapper(self.parent.new_from_list(ElementTemplate['junction']))
        return newObj
    
    